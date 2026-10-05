"""Parse a chapter's unit MCQ source (mcq.md) into mcq.json for build_mcq.js and check_mcq.py.

Usage: python parse_mcq.py <mcq.md> <out.json>

Sections (top-level "# " headings): INSTRUCTIONS, QUESTIONS. See templates/mcq_template.md.
Format errors (a malformed heading or option line, an image without a credit) stop the parse here;
content rules (question count, options, answer balance, lesson coverage) are check_mcq.py's job,
so every rule failure is reported together rather than one at a time.
"""
import json
import os
import re
import sys

from parse_content import find_config, parse_table, split_sections

Q_HEAD = re.compile(r"^##\s+(\d+)\s*\|\s*L(\d+)\s*\|\s*(AO\d)\s*$")
OPTION = re.compile(r"^([A-Z])\.\s+(.+)$")
WHY = re.compile(r"^why\s+([A-Z]):\s*(.*)$")
KEY = re.compile(r"^(answer|source|image|credit|width):\s*(.*)$")


def parse_questions(lines):
    qs, q = [], None
    for n, line in enumerate(lines, 1):
        if line.startswith("## "):
            m = Q_HEAD.match(line)
            if not m:
                sys.exit(f"QUESTIONS line {n}: heading must be \"## <number> | L<lesson> | AO<n>\": {line}")
            q = {"number": int(m.group(1)), "lesson": int(m.group(2)), "ao": m.group(3), "text": [], "table": [],
                 "options": [], "answer": "", "why": {}, "source": "", "image": None, "credit": None, "width": None}
            qs.append(q)
            continue
        if q is None or not line.strip():
            continue
        s = line.strip()
        if (m := OPTION.match(s)):
            q["options"].append({"letter": m.group(1), "text": m.group(2).strip()})
        elif (m := WHY.match(s)):
            q["why"][m.group(1)] = m.group(2).strip()
        elif (m := KEY.match(s)):
            val = m.group(2).strip()
            q[m.group(1)] = float(val) if m.group(1) == "width" else val.upper() if m.group(1) == "answer" else val
        elif s.startswith("|"):
            q["table"].append(s)
        elif q["options"]:
            sys.exit(f"Question {q['number']}: text after the options (options must come last before answer:): {s}")
        else:
            q["text"].append(s)
    for q in qs:
        q["text"] = " ".join(q["text"])
        q["table"] = parse_table(q["table"]) if q["table"] else []
    return qs


def attach_images(qs, base):
    """Resolve image paths (relative to mcq.md), record pixel sizes, require a credit."""
    from PIL import Image
    for q in qs:
        if not q["image"]:
            continue
        path = os.path.normpath(os.path.join(base, q["image"]))
        if not os.path.exists(path):
            sys.exit(f"Question {q['number']}: image not found: {path}")
        if not q["credit"]:
            sys.exit(f"Question {q['number']}: image has no credit: line")
        with Image.open(path) as im:
            q["image_w"], q["image_h"] = im.size
        q["image"] = path


def main(src, dst):
    with open(src, encoding="utf-8-sig") as f:
        front, sections = split_sections(f.read())
    cfg_path = find_config(src, front)
    with open(cfg_path, encoding="utf-8-sig") as f:
        config = json.load(f)
    if "unit_mcq" not in config:
        sys.exit(f"{cfg_path} has no \"unit_mcq\" block (see courses/9618_chapter3.json)")
    for k in ("chapter", "title", "prefix", "minutes", "lessons"):
        if not front.get(k):
            sys.exit(f"mcq.md front matter is missing {k}:")
    front.setdefault("course", config.get("course", ""))
    qs = parse_questions(sections.get("QUESTIONS", []))
    attach_images(qs, os.path.dirname(os.path.abspath(src)))
    credits = {}
    for q in qs:
        if q["image"]:
            credits.setdefault(q["credit"], []).append(str(q["number"]))
    mcq = {
        "config": config,
        "config_path": cfg_path,
        "meta": front,
        "instructions": [l.strip() for l in sections.get("INSTRUCTIONS", []) if l.strip()],
        "questions": qs,
        "credits": [f"Question{'s' if len(n) > 1 else ''} {', '.join(n)}: {c}" for c, n in credits.items()],
    }
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(mcq, f, ensure_ascii=False, indent=1)
    print(f"Parsed {len(qs)} questions -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
