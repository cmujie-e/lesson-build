"""Build and check a lesson bundle from content.md in one command.

Usage:
  python lesson.py build <content.md> [output_folder]   build, check, make inspection sheets
  python lesson.py draft <content.md>                   same, before images are downloaded;
                                                        output goes to out/ only, never the lesson folder
  python lesson.py check <content.md> [output_folder]   checks and inspection sheets only

output_folder defaults to the folder holding content.md. The course rules (word limit, font
size, which documents, file names, lesson length) come from the nearest course.json above
content.md. Stops at the first failed step; exit code 0 only if every check passes.

Steps: parse content.md -> slide deck -> Word documents -> glossary -> PDFs -> render pages
-> slide check -> bundle check -> contact sheets (out/<lesson>/qa) for visual inspection.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
SOFFICE = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.com"
PDFTOPPM = shutil.which("pdftoppm") or r"C:\poppler\poppler-26.09.0\Library\bin\pdftoppm.exe"
WORD_TYPES = {"speaker_notes", "worksheet", "mark_scheme", "lesson_plan", "assessment_plan"}
KNOWN_TYPES = WORD_TYPES | {"deck", "glossary"}


def run(*args, quiet=False, check=True):
    r = subprocess.run([str(a) for a in args], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout.strip() and not quiet:
        print(r.stdout.rstrip())
    if check and r.returncode != 0:
        print(r.stdout if quiet else "", r.stderr)
        sys.exit(f"FAILED: {os.path.basename(str(args[1]))}")
    return r.returncode


def to_pdf(src, outdir):
    run(SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", outdir, src, quiet=True)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
    if not os.path.exists(pdf):
        sys.exit(f"FAILED: PDF conversion of {os.path.basename(src)} (is the file open in another program?)")
    return pdf


def fill(tmpl, meta):
    import re
    return re.sub(r"\{(\w+)\}", lambda m: str(meta.get(m.group(1), m.group(0))), tmpl)


def work_dir(dest, draft):
    d = os.path.abspath(dest.rstrip("\\/"))
    name = (os.path.basename(os.path.dirname(d)) + "_" + os.path.basename(d)).replace(" ", "")
    return os.path.join(HERE, "out", ("draft_" if draft else "") + name)


def build(content, dest, work, draft):
    os.makedirs(work, exist_ok=True)
    os.makedirs(dest, exist_ok=True)
    locked = glob.glob(os.path.join(dest, "~$*"))
    if locked:
        sys.exit(f"FAILED: close these files first (open in Office): {[os.path.basename(f) for f in locked]}")
    lj = os.path.join(work, "lesson.json")
    os.environ.pop("LESSON_DRAFT", None)
    if draft:
        os.environ["LESSON_DRAFT"] = "1"
    print("1. Parse content.md")
    run(PY, "parse_content.py", content, lj)
    L = json.load(open(lj, encoding="utf-8"))
    docs = L["config"]["documents"]
    unknown = [d["type"] for d in docs if d["type"] not in KNOWN_TYPES]
    if unknown:
        sys.exit(f"FAILED: course.json asks for document types this toolkit cannot build yet: {unknown}")
    files = {d["type"]: fill(d["file"], L["meta"]) for d in docs}

    if "deck" in files:
        print("2. Slide deck")
        run(NODE, "build_deck.js", lj, os.path.join(dest, files["deck"]))
    print("3. Word documents")
    run(NODE, "build_docs.js", lj, work)
    if "glossary" in files:
        print("4. Glossary")
        run(PY, "build_glossary.py", lj, os.path.join(dest, files["glossary"]))
    print("5. Word -> delivery format")
    for t in WORD_TYPES & files.keys():
        docx = os.path.join(work, os.path.splitext(files[t])[0] + ".docx")
        if files[t].lower().endswith(".pdf"):
            shutil.copy2(to_pdf(docx, work), dest)
        else:
            shutil.copy2(docx, dest)
        print(f"  {files[t]}")
    return L, files


def render_and_check(dest, work, L, files):
    print("6. Render pages")
    render, qa = os.path.join(work, "render"), os.path.join(work, "qa")
    for d in (render, qa):
        os.makedirs(d, exist_ok=True)
    for f in files.values():
        path = os.path.join(dest, f)
        pdf = path if f.lower().endswith(".pdf") else to_pdf(path, work)
        stem = os.path.splitext(f)[0]
        for old in glob.glob(os.path.join(render, f"{stem}-*.jpg")) + glob.glob(os.path.join(qa, f"{stem}_*.jpg")):
            os.remove(old)
        run(PDFTOPPM, "-jpeg", "-r", "60", pdf, os.path.join(render, stem))
        per = 12 if f.endswith(".pptx") else 8
        run(PY, "montage.py", os.path.join(render, f"{stem}-*.jpg"), os.path.join(qa, stem), 3 if per == 12 else 4, per, quiet=True)
        print(f"  {f}: {len(glob.glob(os.path.join(render, stem + '-*.jpg')))} pages")
    ok = True
    lj = os.path.join(work, "lesson.json")
    if "deck" in files:
        print("\n7. Slide check")
        ok &= run(PY, "check_deck.py", "--config", lj, os.path.join(dest, files["deck"]), check=False) == 0
    print("\n8. Bundle check")
    ok &= run(PY, "check_bundle.py", dest, lj, check=False) == 0
    print(f"\nInspection sheets: {qa}")
    print("RESULT:", "PASS" if ok else "FAIL")
    return ok


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("build", "draft", "check"):
        sys.exit(__doc__)
    mode, content = sys.argv[1], os.path.abspath(sys.argv[2])
    if mode == "draft":
        dest = os.path.join(work_dir(os.path.dirname(content), True), "deliverables")
        work = work_dir(os.path.dirname(content), True)
    else:
        dest = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.dirname(content)
        work = work_dir(dest, False)
    if mode == "check":
        L = json.load(open(os.path.join(work, "lesson.json"), encoding="utf-8"))
        files = {d["type"]: fill(d["file"], L["meta"]) for d in L["config"]["documents"]}
    else:
        L, files = build(content, dest, work, mode == "draft")
    sys.exit(0 if render_and_check(dest, work, L, files) else 1)


if __name__ == "__main__":
    main()
