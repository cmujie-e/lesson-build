"""Build a full seven-document lesson bundle from content.md, following Chapter 3 CLAUDE.md.

Usage: python build_lesson.py <content.md> <output_folder>

Steps:
  1. parse content.md -> lesson.json               (parse_content.py)
  2. slide deck .pptx                               (build_deck.js, pptxgenjs)
  3. speaker notes, worksheet, mark scheme,
     lesson plan, assessment plan .docx             (build_docs.js, docx)
  4. bilingual glossary .xlsx                       (build_glossary.py, openpyxl)
  5. speaker notes + worksheet .docx -> .pdf        (LibreOffice); the .docx intermediates stay in the build folder
  6. render every deliverable to JPEG for visual QA (LibreOffice + pdftoppm) into the build folder
Intermediate files go to lesson-build/out/<folder name>; only the seven deliverables go to <output_folder>.
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


def run(*args):
    r = subprocess.run(list(args), cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout.strip():
        print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(f"FAILED: {' '.join(os.path.basename(a) for a in args[:2])}")


def to_pdf(src, outdir):
    run(SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", outdir, src)
    return os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")


def main(content, dest):
    # e.g. ...\Lesson 2\v2 -> out\Lesson2_v2
    d = os.path.abspath(dest.rstrip("\\/"))
    work = os.path.join(HERE, "out", (os.path.basename(os.path.dirname(d)) + "_" + os.path.basename(d)).replace(" ", ""))
    os.makedirs(work, exist_ok=True)
    os.makedirs(dest, exist_ok=True)
    lj = os.path.join(work, "lesson.json")

    print("1. Parse content.md")
    run(PY, "parse_content.py", content, lj)
    L = json.load(open(lj, encoding="utf-8"))
    p, deck = L["meta"]["prefix"], L["meta"]["deck_name"]

    print("2. Slide deck")
    run(NODE, "build_deck.js", lj, os.path.join(dest, f"{deck}.pptx"))

    print("3. Word documents")
    run(NODE, "build_docs.js", lj, work)
    for name in ("Mark_Scheme", "Lesson_Plan", "Assessment_Plan"):
        shutil.copy2(os.path.join(work, f"{p}_{name}.docx"), dest)

    print("4. Glossary")
    run(PY, "build_glossary.py", lj, os.path.join(dest, f"{p}_Bilingual_Glossary.xlsx"))

    print("5. PDF conversion (speaker notes, worksheet)")
    for name in ("Speaker_Notes", "Worksheet"):
        pdf = to_pdf(os.path.join(work, f"{p}_{name}.docx"), work)
        shutil.copy2(pdf, dest)
        print(f"  {os.path.basename(pdf)}")

    print("6. Render for visual QA")
    render = os.path.join(work, "render")
    os.makedirs(render, exist_ok=True)
    targets = [os.path.join(dest, f"{deck}.pptx"), os.path.join(dest, f"{p}_Bilingual_Glossary.xlsx")] + \
              [os.path.join(dest, f"{p}_{n}.docx") for n in ("Mark_Scheme", "Lesson_Plan", "Assessment_Plan")]
    pdfs = [to_pdf(t, work) for t in targets] + [os.path.join(dest, f"{p}_{n}.pdf") for n in ("Speaker_Notes", "Worksheet")]
    for pdf in pdfs:
        stem = os.path.splitext(os.path.basename(pdf))[0]
        # clear this document's old page images so a shorter rebuild leaves no stale pages
        for old in glob.glob(os.path.join(render, f"{stem}-*.jpg")):
            os.remove(old)
        run(PDFTOPPM, "-jpeg", "-r", "60", pdf, os.path.join(render, stem))
    print(f"  rendered pages -> {render}")
    print(f"Done. Deliverables in {dest}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
