"""Parse a lesson content.md into lesson.json for the builders.

Usage: python parse_content.py <content.md> <out.json>

Sections (top-level "# " headings): SLIDES, WORKSHEET, MARK SCHEME, LESSON PLAN,
ASSESSMENT PLAN, GLOSSARY, GLOSSARY NOTES. See the format guide at the top of content.md.
"@id" references to slide ids are replaced with slide numbers everywhere.
"""
import json
import os
import re
import sys

SLIDE_HEAD = re.compile(r"^##\s+(\w+)\s*\|\s*(.+?)\s*\{#([a-z0-9-]+)\}\s*$")
KEY_LINE = re.compile(r"^(tag|subtitle|diagram|image|credit):\s*(.*)$")


def split_sections(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    front = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            front[k.strip()] = v.strip()
        text = text[m.end():]
    sections, name = {}, None
    for line in text.splitlines():
        if line.startswith("# "):
            name = line[2:].strip().upper()
            sections[name] = []
        elif name:
            sections[name].append(line)
    return front, sections


def parse_table(lines):
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def parse_blocks(lines):
    """Paragraphs, bullet lists and tables for generic document sections."""
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            blocks.append({"type": "table", "rows": parse_table(tbl)})
        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip())
                i += 1
            blocks.append({"type": "bullets", "items": items})
        elif line.strip().startswith("{{") and line.strip().endswith("}}"):
            blocks.append({"type": "placeholder", "name": line.strip()[2:-2]})
            i += 1
        else:
            blocks.append({"type": "para", "text": line.strip()})
            i += 1
    return blocks


def parse_subsections(lines):
    subs, cur = [], None
    pre = []
    for line in lines:
        if line.startswith("## "):
            cur = {"heading": line[3:].strip(), "lines": []}
            subs.append(cur)
        elif line.strip().startswith("{{") and cur is None:
            pre.append(line)
        elif cur is not None:
            # a placeholder line on its own ends the current subsection
            if line.strip().startswith("{{") and line.strip().endswith("}}"):
                subs.append({"heading": None, "lines": [line]})
                cur = {"heading": None, "lines": []}
                subs.append(cur)
            else:
                cur["lines"].append(line)
    out = []
    for s in subs:
        blocks = parse_blocks(s["lines"])
        if s["heading"] is None and not blocks:
            continue
        out.append({"heading": s["heading"], "blocks": blocks})
    return out


def parse_slides(lines):
    slides, cur, in_notes = [], None, False
    for line in lines:
        m = SLIDE_HEAD.match(line)
        if m:
            cur = {"layout": m.group(1), "title": m.group(2), "id": m.group(3),
                   "tag": None, "subtitle": None, "diagram": None, "image": None, "credit": None,
                   "bullets": [], "cards": [], "table": [], "text": [], "notes": []}
            slides.append(cur)
            in_notes = False
            continue
        if cur is None:
            continue
        if in_notes:
            cur["notes"].append(line)
            continue
        if line.strip() == "notes:":
            in_notes = True
            continue
        km = KEY_LINE.match(line)
        if km:
            cur[km.group(1)] = km.group(2).strip()
        elif line.lstrip().startswith("|"):
            cur["table"].append(line)
        elif line.startswith("- "):
            item = line[2:].strip()
            if cur["layout"] == "cards" and "::" in item:
                head, _, detail = item.partition("::")
                cur["cards"].append({"head": head.strip(), "detail": detail.strip()})
            else:
                cur["bullets"].append(item)
        elif line.strip():
            cur["text"].append(line.strip())
    for s in slides:
        s["table"] = parse_table(s["table"]) if s["table"] else []
        s["notes"] = "\n".join(s["notes"]).strip()
    return slides


def attach_images(slides, base):
    """Resolve image paths (relative to content.md), record pixel sizes, put each credit
    in its slide's notes and append the exempt "Image credits" slide. Fails if an image
    is missing or has no credit, so an uncredited image can never reach a deck."""
    from PIL import Image
    credits = []
    for n, s in enumerate(slides, 1):
        if not s["image"]:
            continue
        path = os.path.normpath(os.path.join(base, s["image"]))
        if not os.path.exists(path):
            sys.exit(f"Slide {n} ({s['id']}): image not found: {path}")
        if not s["credit"]:
            sys.exit(f"Slide {n} ({s['id']}): image has no credit: line")
        with Image.open(path) as im:
            s["image_w"], s["image_h"] = im.size
        s["image"] = path
        s["notes"] = f"{s['notes']}\nImage: {s['credit']}".strip()
        credits.append(f"Slide {n}: {s['credit']}")
    if credits:
        slides.append({
            "layout": "credits", "title": "Image credits", "id": "credits", "tag": "CREDITS",
            "subtitle": None, "diagram": None, "image": None, "credit": None,
            "bullets": credits, "cards": [], "table": [], "text": [],
            "notes": "Image credits for every image in this deck. This slide is exempt from the 30 pt and "
                     "35-word rules (Chapter 3 CLAUDE.md). Textbook figures are used under the school's licence.",
        })
    return slides


def parse_worksheet(lines):
    ws = {"intro": "", "sections": []}
    sec, q = None, None
    ref_lines = []
    for line in lines:
        if line.startswith("### "):
            letter, _, marks = line[4:].partition("|")
            q = {"item": letter.strip(), "marks": int(marks.strip()), "text": [], "answer": "",
                 "marking": "", "lines": None}
            sec["questions"].append(q)
        elif line.startswith("## "):
            letter, _, name = line[3:].partition("|")
            sec = {"letter": letter.strip(), "name": name.strip(), "wordbank": "", "instructions": [],
                   "reference_title": "", "reference": [], "questions": []}
            ws["sections"].append(sec)
            q = None
        elif sec is None:
            if line.startswith("intro:"):
                ws["intro"] = line[6:].strip()
        elif q is None:
            if line.startswith("wordbank:"):
                sec["wordbank"] = line[9:].strip()
            elif line.startswith("reference:"):
                sec["reference_title"] = line[10:].strip()
            elif line.lstrip().startswith("|"):
                sec["reference"].append(line)
            elif line.strip():
                sec["instructions"].append(line.strip())
        else:
            for key in ("answer", "marking", "lines"):
                if line.startswith(key + ":"):
                    val = line[len(key) + 1:].strip()
                    q[key] = int(val) if key == "lines" else val
                    break
            else:
                if line.strip():
                    q["text"].append(line.strip())
    for sec in ws["sections"]:
        sec["reference"] = parse_table(sec["reference"]) if sec["reference"] else []
        sec["marks"] = sum(q["marks"] for q in sec["questions"])
        for q in sec["questions"]:
            q["text"] = " ".join(q["text"])
            if q["lines"] is None:
                q["lines"] = q["marks"] + 1
    ws["total"] = sum(s["marks"] for s in ws["sections"])
    return ws


def resolve_refs(obj, ids):
    def sub(s):
        return re.sub(r"@([a-z0-9]+(?:-[a-z0-9]+)*)",
                      lambda m: str(ids[m.group(1)]) if m.group(1) in ids else m.group(0), s)
    if isinstance(obj, str):
        return sub(obj)
    if isinstance(obj, list):
        return [resolve_refs(x, ids) for x in obj]
    if isinstance(obj, dict):
        return {k: resolve_refs(v, ids) for k, v in obj.items()}
    return obj


def main(src, dst):
    with open(src, encoding="utf-8") as f:
        front, sections = split_sections(f.read())
    slides = attach_images(parse_slides(sections.get("SLIDES", [])), os.path.dirname(os.path.abspath(src)))
    ids = {s["id"]: i for i, s in enumerate(slides, 1)}
    if len(ids) != len(slides):
        sys.exit("Duplicate slide id in content.md")
    ms_note = next((l[5:].strip() for l in sections.get("MARK SCHEME", []) if l.startswith("note:")), "")
    gloss = [l for l in sections.get("GLOSSARY", []) if l.lstrip().startswith("|")]
    lesson = {
        "meta": front,
        "slides": slides,
        "worksheet": parse_worksheet(sections.get("WORKSHEET", [])),
        "mark_scheme_note": ms_note,
        "lesson_plan": parse_subsections(sections.get("LESSON PLAN", [])),
        "assessment_plan": parse_subsections(sections.get("ASSESSMENT PLAN", [])),
        "glossary": parse_table(gloss),
        "glossary_notes": [l.strip() for l in sections.get("GLOSSARY NOTES", []) if l.strip()],
    }
    lesson = resolve_refs(lesson, ids)
    unresolved = sorted(set(re.findall(r"@([a-z][a-z0-9-]*)", json.dumps(lesson, ensure_ascii=False))))
    if unresolved:
        sys.exit(f"Unresolved slide references: {unresolved}")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=1)
    print(f"Parsed {len(slides)} slides, worksheet {lesson['worksheet']['total']} marks, "
          f"{len(lesson['glossary']) - 1} glossary terms -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
