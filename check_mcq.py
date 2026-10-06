"""Unit MCQ checks against the "unit_mcq" rules in course.json (run by `lesson.py mcq`).

Usage: python check_mcq.py <output_folder> <mcq.json>

Checks:
  1. both deliverables exist (question paper, answer key)
  2. question count within min_questions..max_questions, numbered 1..N in order
  3. every question: a stem, exactly `options` options lettered A, B, C ..., no duplicate options,
     a correct letter that is one of them, a "why" for every wrong option (and none for the correct one)
  4. every lesson 1..`lessons` (front matter) has at least one question; none outside that range
  5. answer balance: no letter correct for more than max_letter_share of questions,
     no more than max_run consecutive questions with the same correct letter
  6. question paper carries no answers: no "why" or source text, nothing written in the answer grid
  7. answer key letters match mcq.md, question by question
  8. no placeholder text (lorem, TODO, [insert, {{ }}) in either document
"""
import json
import os
import re
import string
import subprocess
import sys
from markitdown import MarkItDown

from toolpaths import PDFTOTEXT  # poppler, not Git's xpdf copy (see toolpaths.py)

folder, mj = sys.argv[1], sys.argv[2]
M = json.load(open(mj, encoding="utf-8"))
rules = M["config"]["unit_mcq"]
fill = lambda t: re.sub(r"\{(\w+)\}", lambda m: str(M["meta"].get(m.group(1), m.group(0))), t)
files = {d["type"]: fill(d["file"]) for d in rules["documents"]}
flat = lambda s: re.sub(r"\s+", " ", s).strip()
qs = M["questions"]
fails = []


def report(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{': ' + detail if detail else ''}")
    if not ok:
        fails.append(name)


def read(path):
    if path.endswith(".pdf"):
        return subprocess.run([PDFTOTEXT, "-enc", "UTF-8", path, "-"], capture_output=True, text=True, encoding="utf-8").stdout
    return MarkItDown().convert(path).text_content


missing = [f for f in files.values() if not os.path.exists(os.path.join(folder, f))]
report("Question paper and answer key present", not missing, f"missing {missing}" if missing else "")
raw = {t: read(os.path.join(folder, f)) for t, f in files.items() if os.path.exists(os.path.join(folder, f))}

# 2. count and numbering
lo, hi = rules["min_questions"], rules["max_questions"]
report(f"{lo}-{hi} questions", lo <= len(qs) <= hi, f"{len(qs)} questions")
numbers = [q["number"] for q in qs]
report("Questions numbered 1..N in order", numbers == list(range(1, len(qs) + 1)),
       "" if numbers == list(range(1, len(qs) + 1)) else f"found {numbers}")

# 3. structure of each question
letters = list(string.ascii_uppercase[:rules["options"]])
bad = []
for q in qs:
    n, got = q["number"], [o["letter"] for o in q["options"]]
    texts = [flat(o["text"]).lower() for o in q["options"]]
    if not q["text"]:
        bad.append(f"Q{n} has no question text")
    if got != letters:
        bad.append(f"Q{n} options {''.join(got) or 'none'}, expected {''.join(letters)}")
    if len(set(texts)) != len(texts):
        bad.append(f"Q{n} has duplicate options")
    if q["answer"] not in letters:
        bad.append(f"Q{n} answer '{q['answer']}' is not one of {''.join(letters)}")
    no_why = [l for l in letters if l != q["answer"] and not q["why"].get(l)]
    if no_why:
        bad.append(f"Q{n} no 'why' for wrong option(s) {''.join(no_why)}")
    if q["answer"] in q["why"]:
        bad.append(f"Q{n} has a 'why' for its correct answer {q['answer']}")
report(f"Every question has {len(letters)} distinct options, one correct letter, a reason per wrong option", not bad, "; ".join(bad))

# 4. lesson coverage
lessons = int(M["meta"]["lessons"])
uncovered = [l for l in range(1, lessons + 1) if not any(q["lesson"] == l for q in qs)]
outside = sorted({q["lesson"] for q in qs if not 1 <= q["lesson"] <= lessons})
report(f"Every lesson 1-{lessons} has a question", not uncovered and not outside,
       (f"no question for L{', L'.join(map(str, uncovered))}" if uncovered else "")
       + (f"; lessons outside 1-{lessons}: {outside}" if outside else ""))

# 5. answer balance
answers = [q["answer"] for q in qs]
share, max_run = rules["max_letter_share"], rules["max_run"]
counts = {l: answers.count(l) for l in letters}
over = {l: c for l, c in counts.items() if qs and c / len(qs) > share}
report(f"No letter correct for more than {round(share * 100)}% of questions", not over,
       ", ".join(f"{l}={c}" for l, c in counts.items()))
runs, start = [], 0
for i in range(1, len(answers) + 1):
    if i == len(answers) or answers[i] != answers[start]:
        if i - start > max_run:
            runs.append(f"Q{start + 1}-Q{i} all {answers[start]}")
        start = i
report(f"No more than {max_run} consecutive questions share a correct letter", not runs, "; ".join(runs))

# 6. paper carries no answers
if "mcq_paper" in raw:
    paper = flat(raw["mcq_paper"])
    # whole lines: a "why" often opens by restating its option, which is rightly on the paper
    leaked = [f"Q{q['number']} why {l}" for q in qs for l, w in q["why"].items() if len(w) > 12 and flat(w) in paper]
    leaked += [f"Q{q['number']} source" for q in qs if len(q["source"]) > 12 and flat(q["source"]) in paper]
    grid = paper.rsplit("Answer grid", 1)[-1] if "Answer grid" in paper else ""
    grid = re.sub(r"Image credits\..*", "", grid)
    written = re.findall(r"(?<![\w.])[A-Z](?![\w.])", grid)
    if not grid:
        leaked.append("no answer grid found")
    elif written:
        leaked.append(f"letters in the answer grid: {''.join(written)}")
    if re.search(r"answer:|Answer key|\bCorrect\.", paper):
        leaked.append("answer-key wording on the paper")
    report("Question paper carries no answers", not leaked, "; ".join(leaked))

# 7. key letters match the source
if "mcq_key" in raw:
    key = dict(re.findall(r"^\|\s*(\d+)\s*\|\s*([A-Z])\s*\|\s*L\d+\s*\|", raw["mcq_key"], re.M))
    wrong = [f"Q{q['number']} key {key.get(str(q['number']), 'missing')}, mcq.md {q['answer']}"
             for q in qs if key.get(str(q["number"])) != q["answer"]]
    report("Answer key letters match mcq.md", not wrong and len(key) == len(qs), "; ".join(wrong) or f"{len(key)} letters")

bad = {f: m.group(0) for f, t in raw.items() if (m := re.search(r"lorem|ipsum|\bTODO\b|\[insert|\{\{", t, re.I))}
report("No placeholder text", not bad, str(bad) if bad else "")

print("\nRESULT:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
