"""Bundle-level checks against the course rules in course.json (run by lesson.py).

Usage: python check_bundle.py <output_folder> <lesson.json>

Checks (each only when the course has the documents involved):
  1. exactly the deliverables listed in course.json exist (content.md and subfolders are ignored)
  2. mark scheme and assessment plan both contain every worksheet answer
  3. mark scheme marks add up to the worksheet total
  4. worksheet contains no answers
  5. lesson plan timing covers exactly lesson_minutes with no gaps, and practice meets
     min_practice_minutes
  6. no placeholder text (lorem, TODO, [insert, {{ }}) in any deliverable
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
cfg = L["config"]
fill = lambda t: re.sub(r"\{(\w+)\}", lambda m: str(L["meta"].get(m.group(1), m.group(0))), t)
files = {d["type"]: fill(d["file"]) for d in cfg["documents"]}
expected = set(files.values())
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


present = {f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))
           and f != "content.md" and not f.startswith("~$")}
report(f"{len(expected)} deliverables present", present == expected,
       f"{len(present)} files" + (f"; missing {sorted(expected - present)}" if expected - present else "")
       + (f"; unexpected {sorted(present - expected)}" if present - expected else ""))

qs = [q for s in L["worksheet"]["sections"] for q in s["questions"]]
ms, ap, ws = (text.get(files.get(t, ""), "") for t in ("mark_scheme", "assessment_plan", "worksheet"))
if "mark_scheme" in files and "assessment_plan" in files:
    missing = [q["item"] for q in qs if flat(q["answer"]) not in ms or flat(q["answer"]) not in ap]
    report("Mark scheme and assessment plan give identical answers", not missing,
           f"{len(qs)} items" + (f"; mismatched {missing}" if missing else ""))
if "mark_scheme" in files:
    ms_marks = [int(m) for m in re.findall(r"\| (\d+) \|", ms)]
    report("Mark scheme marks match worksheet", sum(ms_marks) == L["worksheet"]["total"],
           f"mark scheme items sum to {sum(ms_marks)}, worksheet total {L['worksheet']['total']}")
if "worksheet" in files:
    leaked = [q["item"] for q in qs if len(q["answer"]) > 12 and flat(q["answer"])[:40] in ws]
    report("Worksheet carries no answers", not leaked, ", ".join(leaked))

if "lesson_plan" in files:
    minutes, practice_min = cfg.get("lesson_minutes", 70), cfg.get("min_practice_minutes", 0)
    timing = next((b for s in L["lesson_plan"] if s["heading"] == "Timing" for b in s["blocks"] if b["type"] == "table"), None)
    if timing is None:
        report("Lesson plan has a Timing table", False)
    else:
        rows = timing["rows"][1:]
        mins = sum(int(r[2]) for r in rows)
        contiguous = all(int(rows[i][1]) == int(rows[i + 1][0]) for i in range(len(rows) - 1))
        spans = all(int(r[1]) - int(r[0]) == int(r[2]) for r in rows)
        report(f"Lesson plan timing = {minutes} minutes",
               mins == minutes and contiguous and spans and rows[0][0] == "0" and rows[-1][1] == str(minutes),
               f"{mins} min over {len(rows)} phases, contiguous={contiguous}, start/end/min consistent={spans}")
        practice = sum(int(r[2]) for r in rows if "practice" in r[3].lower())
        if practice_min:
            report(f"Independent practice >= {practice_min} minutes", practice >= practice_min, f"{practice} min")

bad = {f: m.group(0) for f, t in text.items() if (m := re.search(r"lorem|ipsum|\bTODO\b|\[insert|\{\{", t, re.I))}
report("No placeholder text", not bad, str(bad) if bad else "")

print("\nRESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
