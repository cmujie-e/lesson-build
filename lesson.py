"""Build and check a lesson bundle from content.md in one command.

Usage:
  python lesson.py build <content.md> [output_folder]   build, check, make inspection sheets
  python lesson.py draft <content.md>                   same, before images are downloaded;
                                                        output goes to out/ only, never the lesson folder
  python lesson.py check <content.md> [output_folder]   checks and inspection sheets only
  python lesson.py outline <content.md>                 one-page review summary (out/<lesson>/review.md)
  python lesson.py mcq <mcq.md> [output_folder]         chapter unit MCQ: question paper + answer key, checked
  python lesson.py form <mcq.md>                        Google Forms version of the unit MCQ (Apps Script)
  python lesson.py guide <guide.md> [out.docx]          teacher guide (Word) + page renders for inspection
  python lesson.py glossary-review <chapter folder>     review workbook of every glossary term, for colleagues

output_folder defaults to the folder holding content.md. The course rules (word limit, font
size, which documents, file names, lesson length) come from the nearest course.json above
content.md. Stops at the first failed step; exit code 0 only if every check passes.

Steps: parse content.md -> slide deck -> Word documents -> glossary -> PDFs -> render pages
-> slide check -> bundle check -> layout check -> glossary consistency across lessons
-> contact sheets (out/<lesson>/qa) for visual inspection.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
from toolpaths import NODE, SOFFICE
from toolpaths import PDFTOPPM  # poppler, not Git's xpdf copy (see toolpaths.py)
WORD_TYPES = {"speaker_notes", "worksheet", "mark_scheme", "lesson_plan", "assessment_plan"}
KNOWN_TYPES = WORD_TYPES | {"deck", "glossary"}


def run(*args, quiet=False, check=True):
    # children print UTF-8 (slide titles may hold arrows etc.); without this a pipe defaults to cp1252 on Windows
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([str(a) for a in args], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if r.stdout.strip() and not quiet:
        print(r.stdout.rstrip())
    if check and r.returncode != 0:
        print(r.stdout if quiet else "", r.stderr)
        sys.exit(f"FAILED: {os.path.basename(str(args[1]))}")
    if not check and r.returncode != 0 and r.stderr.strip():
        print(r.stderr.rstrip())  # e.g. a sys.exit("...") message from a sub-script
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


def render_and_check(dest, work, L, files, content):
    print("6. Render pages")
    render, qa = os.path.join(work, "render"), os.path.join(work, "qa")
    for d in (render, qa):
        os.makedirs(d, exist_ok=True)
    pdfs = {}
    for t, f in files.items():
        path = os.path.join(dest, f)
        pdf = path if f.lower().endswith(".pdf") else to_pdf(path, work)
        pdfs[t] = pdf
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
    print("\n9. Layout check")
    docs = [("sheet:" if t == "glossary" else "") + p for t, p in pdfs.items() if t != "deck"]
    ok &= run(PY, "check_layout.py", lj, pdfs.get("deck", "-"), *docs, check=False) == 0
    if "glossary" in files:
        print("\n10. Glossary consistency")
        ok &= run(PY, "check_glossary.py", content, check=False) == 0
    print(f"\nInspection sheets: {qa}")
    print("RESULT:", "PASS" if ok else "FAIL")
    return ok


def mcq(src, dest):
    """Unit MCQ: parse mcq.md -> paper + key (Word) -> paper to PDF -> render -> MCQ and layout checks."""
    work = work_dir(dest, False)
    os.makedirs(work, exist_ok=True)
    os.makedirs(dest, exist_ok=True)  # else shutil.copy2 writes the key to a FILE named like the folder
    locked = glob.glob(os.path.join(dest, "~$*"))
    if locked:
        sys.exit(f"FAILED: close these files first (open in Office): {[os.path.basename(f) for f in locked]}")
    mj = os.path.join(work, "mcq.json")
    print("1. Parse mcq.md")
    run(PY, "parse_mcq.py", src, mj)
    M = json.load(open(mj, encoding="utf-8"))
    files = {d["type"]: fill(d["file"], M["meta"]) for d in M["config"]["unit_mcq"]["documents"]}
    print("2. Word documents")
    run(NODE, "build_mcq.js", mj, work)
    print("3. Word -> delivery format")
    pdfs = {}
    for t, f in files.items():
        docx = os.path.join(work, os.path.splitext(f)[0] + ".docx")
        if f.lower().endswith(".pdf"):
            pdfs[t] = to_pdf(docx, work)
            shutil.copy2(pdfs[t], dest)
        else:
            shutil.copy2(docx, dest)
            pdfs[t] = to_pdf(os.path.join(dest, f), work)
        print(f"  {f}")
    print("4. Render pages")
    render, qa = os.path.join(work, "render"), os.path.join(work, "qa")
    for d in (render, qa):
        os.makedirs(d, exist_ok=True)
    for t, f in files.items():
        stem = os.path.splitext(f)[0]
        for old in glob.glob(os.path.join(render, f"{stem}-*.jpg")) + glob.glob(os.path.join(qa, f"{stem}_[0-9]*.jpg")):
            os.remove(old)
        run(PDFTOPPM, "-jpeg", "-r", "60", pdfs[t], os.path.join(render, stem))
        run(PY, "montage.py", os.path.join(render, f"{stem}-*.jpg"), os.path.join(qa, stem), 4, 8, quiet=True)
        print(f"  {f}: {len(glob.glob(os.path.join(render, stem + '-[0-9]*.jpg')))} pages")
    print("\n5. MCQ check")
    ok = run(PY, "check_mcq.py", dest, mj, check=False) == 0
    print("\n6. Layout check")
    ok &= run(PY, "check_layout.py", mj, "-", *pdfs.values(), check=False) == 0
    print(f"\nInspection sheets: {qa}")
    print("RESULT:", "PASS" if ok else "FAIL")
    return ok


def guide(src, out=None):
    """Teacher guide: guide.md -> Word (build_guide.py) -> PDF -> page renders + contact sheet to inspect.
    Default output: a source in <chapter>/Teacher Guides/_source/ builds into <chapter>/Teacher Guides/."""
    if out is None:
        folder = os.path.dirname(src)
        if os.path.basename(folder) == "_source":
            folder = os.path.dirname(folder)
        out = os.path.join(folder, os.path.splitext(os.path.basename(src))[0] + ".docx")
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(os.path.join(os.path.dirname(out), "~$" + os.path.basename(out)[2:])):
        sys.exit(f"FAILED: close {os.path.basename(out)} in Word first")
    stem = os.path.splitext(os.path.basename(out))[0]
    work = os.path.join(HERE, "out", "guide_" + stem)
    os.makedirs(work, exist_ok=True)
    print("1. Build Word document")
    run(PY, "build_guide.py", src, out)
    print("2. Render pages")
    pdf = to_pdf(out, work)
    for old in glob.glob(os.path.join(work, f"{stem}-*.jpg")) + glob.glob(os.path.join(work, f"{stem}_qa_*.jpg")):
        os.remove(old)
    run(PDFTOPPM, "-jpeg", "-r", "60", pdf, os.path.join(work, stem))
    pages = glob.glob(os.path.join(work, f"{stem}-*.jpg"))
    run(PY, "montage.py", os.path.join(work, f"{stem}-*.jpg"), os.path.join(work, stem + "_qa"), 4, 8, quiet=True)
    print(f"  {len(pages)} pages; inspection sheets: {work}")
    return True


def main():
    # output may go to a file or pipe with a non-UTF-8 code page (cp1252), which cannot print the check reports
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 3 or sys.argv[1] not in ("build", "draft", "check", "outline", "mcq", "form", "guide", "glossary-review"):
        sys.exit(__doc__)
    mode, content = sys.argv[1], os.path.abspath(sys.argv[2])
    if mode == "form":
        sys.exit(run(PY, "make_form.py", content, check=False))
    if mode == "glossary-review":
        sys.exit(run(PY, "glossary_review.py", content, check=False))
    if mode == "guide":
        sys.exit(0 if guide(content, sys.argv[3] if len(sys.argv) > 3 else None) else 1)
    if mode == "mcq":
        dest = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.dirname(content)
        sys.exit(0 if mcq(content, dest) else 1)
    if mode == "outline":
        sys.exit(run(PY, "outline.py", content, check=False))
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
    sys.exit(0 if render_and_check(dest, work, L, files, content) else 1)


if __name__ == "__main__":
    main()
