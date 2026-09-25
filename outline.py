"""One-page review summary of a lesson, for the teacher's review stop.

Usage: python outline.py <content.md>        (or: python lesson.py outline <content.md>)
Writes out/<lesson>/review.md and prints it: every slide's on-screen text, each question with
its answer, the worksheet (question, answer, marks), the timing, the images with their credits
and download status, and the glossary terms. Works before images are downloaded.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def lesson_json(content):
    d = os.path.dirname(os.path.abspath(content))
    name = (os.path.basename(os.path.dirname(d)) + "_" + os.path.basename(d)).replace(" ", "")
    out = os.path.join(HERE, "out", "review_" + name)
    os.makedirs(out, exist_ok=True)
    lj = os.path.join(out, "lesson.json")
    env = dict(os.environ, LESSON_DRAFT="1")
    r = subprocess.run([sys.executable, os.path.join(HERE, "parse_content.py"), content, lj], capture_output=True,
                       text=True, encoding="utf-8", env=env)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    return json.load(open(lj, encoding="utf-8")), out, content


def cell(s):
    return str(s).replace("|", "/").replace("\n", " ")


def answer_from(notes):
    m = re.search(r"Answer:\s*(.+)", notes)
    return m.group(1).strip() if m else "(no answer in notes)"


def main(content):
    L, out, content = lesson_json(content)
    m, cfg = L["meta"], L["config"]
    qtags = set(cfg.get("slides", {}).get("question_tags", []))
    base = os.path.dirname(os.path.abspath(content))
    lines = [f"# Lesson {m['lesson']}: {m['topic']} — review summary", "",
             f"{len(L['slides'])} slides · worksheet {L['worksheet']['total']} marks · "
             f"{len(L['glossary']) - 1} glossary terms · source: {m.get('source', '')}", "",
             "## Slides", "", "| # | Title | Tag | On the slide |", "|---|---|---|---|"]
    for i, s in enumerate(L["slides"], 1):
        body = s["text"] + s["bullets"] + [f"{c['head']}: {c['detail']}" for c in s["cards"]] \
            + [" / ".join(r) for r in s["table"]] + ([f"[image] {os.path.basename(s['image'])}"] if s.get("image") else [])
        lines.append(f"| {i} | {cell(s['title'])} | {s.get('tag') or ''} | {cell(' · '.join(body))[:260]} |")
    lines += ["", "## Questions and answers", ""]
    for i, s in enumerate(L["slides"], 1):
        if s.get("tag") in qtags:
            q = " ".join(s["text"] + s["bullets"])
            lines.append(f"- **Slide {i} ({s['tag']}):** {q}  \n  **Answer:** {answer_from(s['notes'])}")
    lines += ["", "## Worksheet", "", "| Item | Marks | Question | Answer |", "|---|---|---|---|"]
    for sec in L["worksheet"]["sections"]:
        lines.append(f"| **{sec['letter']}** | **{sec['marks']}** | **{cell(sec['name'])}** | |")
        for q in sec["questions"]:
            lines.append(f"| {q['item']} | {q['marks']} | {cell(q['text'])} | {cell(q['answer'])} |")
    timing = next((b for s in L["lesson_plan"] if s["heading"] == "Timing" for b in s["blocks"] if b["type"] == "table"), None)
    if timing:
        lines += ["", "## Timing", "", "| " + " | ".join(timing["rows"][0]) + " |", "|" + "---|" * len(timing["rows"][0])]
        lines += ["| " + " | ".join(cell(c) for c in r) + " |" for r in timing["rows"][1:]]
    lines += ["", "## Images", "", "| Where | File | Downloaded | Credit |", "|---|---|---|---|"]
    raw = open(content, encoding="utf-8-sig").read()
    for block in re.split(r"\n(?=##+ )", raw):
        img = re.search(r"^image:\s*(.+)$", block, re.M)
        if img:
            head = block.splitlines()[0]
            where = (re.search(r"\{#([a-z0-9-]+)\}", head) or re.search(r"^##\s+(\w+)", head)).group(1)
            path = os.path.normpath(os.path.join(base, img.group(1).strip()))
            cred = re.search(r"^credit:\s*(.+)$", block, re.M)
            lines.append(f"| {where} | {os.path.basename(path)} | {'yes' if os.path.exists(path) else 'no'} | "
                         f"{cell(cred.group(1)) if cred else 'MISSING'} |")
    lines += ["", "## Glossary terms", "", ", ".join(r[0] for r in L["glossary"][1:])]
    text = "\n".join(lines) + "\n"
    path = os.path.join(out, "review.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print(f"Saved: {path}")


if __name__ == "__main__":
    main(sys.argv[1])
