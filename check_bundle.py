"""Bundle-level checks against Chapter 3 CLAUDE.md (run after build_lesson.py).

Usage: python check_bundle.py <output_folder> <lesson.json>

Checks:
  1. exactly the seven deliverables exist, named <prefix>_... (content.md is the source and is ignored)
  2. mark scheme and assessment plan both contain every worksheet answer, with the same marks
  3. worksheet PDF contains no answers
  4. lesson plan timing adds up to 70 minutes with no gaps
  5. no placeholder text (lorem, TODO, [insert, {{ }}) in any deliverable
"""
import json
import os
import re
import shutil
import subprocess
import sys
from markitdown import MarkItDown

folder, lj = sys.argv[1], sys.argv[2]
L = json.load(open(lj, encoding="utf-8"))
p, deck = L["meta"]["prefix"], L["meta"]["deck_name"]
expected = {f"{deck}.pptx", f"{p}_Speaker_Notes.pdf", f"{p}_Bilingual_Glossary.xlsx", f"{p}_Worksheet.pdf",
            f"{p}_Mark_Scheme.docx", f"{p}_Lesson_Plan.docx", f"{p}_Assessment_Plan.docx"}
md = MarkItDown()
PDFTOTEXT = shutil.which("pdftotext") or r"C:\poppler\poppler-26.09.0\Library\bin\pdftotext.exe"
flat = lambda s: re.sub(r"\s+", " ", s).strip()


def read(path):
    """PDFs via poppler's pdftotext (markitdown needs an extra package for PDF); Office files via markitdown."""
    if path.endswith(".pdf"):
        return subprocess.run([PDFTOTEXT, "-enc", "UTF-8", path, "-"], capture_output=True, text=True, encoding="utf-8").stdout
    return md.convert(path).text_content


text = {f: flat(read(os.path.join(folder, f))) for f in sorted(expected) if os.path.exists(os.path.join(folder, f))}
fails = []


def report(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{': ' + detail if detail else ''}")
    if not ok:
        fails.append(name)


present = {f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f != "content.md"}
report("Seven deliverables present", present == expected,
       f"{len(present)} files" + (f"; missing {sorted(expected - present)}" if expected - present else "")
       + (f"; unexpected {sorted(present - expected)}" if present - expected else ""))

ms, ap, ws = text.get(f"{p}_Mark_Scheme.docx", ""), text.get(f"{p}_Assessment_Plan.docx", ""), text.get(f"{p}_Worksheet.pdf", "")
qs = [q for s in L["worksheet"]["sections"] for q in s["questions"]]
missing = [q["item"] for q in qs if flat(q["answer"]) not in ms or flat(q["answer"]) not in ap]
report("Mark scheme and assessment plan give identical answers", not missing, f"{len(qs)} items" + (f"; mismatched {missing}" if missing else ""))
ms_marks = [int(m) for m in re.findall(r"\| (\d+) \|", ms)]
report("Mark scheme marks match worksheet", sum(ms_marks) == L["worksheet"]["total"],
       f"mark scheme items sum to {sum(ms_marks)}, worksheet total {L['worksheet']['total']}")
leaked = [q["item"] for q in qs if len(q["answer"]) > 12 and flat(q["answer"])[:40] in ws]
report("Worksheet carries no answers", not leaked, ", ".join(leaked))

timing = next(b for s in L["lesson_plan"] if s["heading"] == "Timing" for b in s["blocks"] if b["type"] == "table")
rows = timing["rows"][1:]
mins = sum(int(r[2]) for r in rows)
contiguous = all(int(rows[i][1]) == int(rows[i + 1][0]) for i in range(len(rows) - 1))
spans = all(int(r[1]) - int(r[0]) == int(r[2]) for r in rows)
report("Lesson plan timing = 70 minutes", mins == 70 and contiguous and spans and rows[0][0] == "0" and rows[-1][1] == "70",
       f"{mins} min over {len(rows)} phases, contiguous={contiguous}, start/end/min consistent={spans}")

bad = {f: m.group(0) for f, t in text.items() if (m := re.search(r"lorem|ipsum|\bTODO\b|\[insert|\{\{", t, re.I))}
report("No placeholder text", not bad, str(bad) if bad else "")

print("\nRESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
