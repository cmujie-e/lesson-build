"""Chapter glossary review workbook for native-speaker colleagues (run by `lesson.py glossary-review`).

Usage: python glossary_review.py <chapter folder>

Collects the GLOSSARY table from every lesson's content.md in the chapter folder (skipping _archive,
_duplicates and out folders), one row per unique term, and writes
<chapter folder>\\Chapter<N>_Glossary_Review.xlsx with a "Read me" sheet and one review sheet per
language: term, definition, lessons, machine translation, "check first" reason, Verdict dropdown
(Correct / Change / Unsure), suggested translation, comment. Stops if a repeated term has different
translations in different lessons (fix that first; check_glossary.py reports it too).

"Check first" rows (shaded, listed first) come from either source:
  1. lines in a lesson's GLOSSARY NOTES of the form
       Check first (Thai): Term — reason; Other term — reason
       Check first (Chinese): Term — reason
       Check first (both): Term — reason
  2. an optional <chapter folder>\\glossary_flags.json:
       {"Thai": {"term": "reason", ...}, "Chinese": {...},
        "contains": {"Thai": {"text in translation": "reason"}}}
Language columns are the 3rd and 4th columns of the glossary table; their names come from its header.
"""
import glob
import json
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_content import split_sections  # noqa: E402

NAVY, HDR, FLAG, ALT = "1E2761", "3A4488", "FFF6E0", "F4F6FC"
LANG_NAMES = ("Thai", "Chinese")  # short names used in flags and sheet names
LANG_LABEL = {"Thai": "Thai", "Chinese": "Chinese (Simplified)"}


def key(term):
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", term)).strip().lower()


def lesson_files(chapter):
    found = []
    for p in glob.glob(os.path.join(chapter, "**", "content.md"), recursive=True):
        rel = os.path.relpath(p, chapter)  # only folders inside the chapter count
        if re.search(r"(^|[\\/])(_archive|_duplicates|out|_build)[\\/]", rel):
            continue
        with open(p, encoding="utf-8-sig") as f:
            front, sections = split_sections(f.read())
        if "GLOSSARY" in sections and front.get("lesson", "").isdigit():
            found.append((int(front["lesson"]), front.get("chapter", ""), p, sections))
    nums = [n for n, *_ in found]
    dup = sorted({n for n in nums if nums.count(n) > 1})
    if dup:
        sys.exit(f"More than one content.md for lesson(s) {dup}; move old copies to _archive first")
    return sorted(found)


def main(chapter):
    chapter = os.path.abspath(chapter)
    lessons = lesson_files(chapter)
    if not lessons:
        sys.exit(f"No lesson content.md with a GLOSSARY found under {chapter}")
    chapter_no = lessons[0][1] or re.sub(r"\D", "", os.path.basename(chapter))
    course = ""
    cj = os.path.join(chapter, "course.json")
    if os.path.exists(cj):
        course = json.load(open(cj, encoding="utf-8-sig")).get("course", "")
    course = course or "Cambridge International AS Level Computer Science (9618)"
    terms, flags, langs = {}, {"Thai": {}, "Chinese": {}}, None
    for n, _, path, sections in lessons:
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in sections["GLOSSARY"] if l.lstrip().startswith("|")]
        header, body = rows[0], rows[1:]
        if langs is None:
            langs = header[2:4]
        for r in body:
            k = key(r[0])
            if k not in terms:
                terms[k] = {"term": r[0], "definition": r[1], "tr": r[2:4], "lessons": []}
            elif terms[k]["tr"] != r[2:4]:
                sys.exit(f"'{r[0]}' has different translations in different lessons (Lesson {n}); fix before review")
            terms[k]["lessons"].append(n)
        for line in sections.get("GLOSSARY NOTES", []):
            m = re.match(r"\s*Check first \((Thai|Chinese|both)\):\s*(.+)$", line, re.I)
            if not m:
                continue
            targets = LANG_NAMES if m.group(1).lower() == "both" else (m.group(1).title(),)
            for item in m.group(2).split(";"):
                term, _, reason = item.partition("—")
                for lang in targets:
                    flags[lang][key(term)] = f"{reason.strip() or 'Flagged'} (Lesson {n} note)."
    contains = {}
    fj = os.path.join(chapter, "glossary_flags.json")
    if os.path.exists(fj):
        data = json.load(open(fj, encoding="utf-8"))
        for lang in LANG_NAMES:
            flags[lang].update({key(t): r for t, r in data.get(lang, {}).items()})
        contains = data.get("contains", {})
    unknown = [t for lang in LANG_NAMES for t in flags[lang] if t not in terms]
    if unknown:
        sys.exit(f"Flagged terms not in any glossary: {unknown}")

    thin = Side(style="thin", color="CADCFC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")
    wb = Workbook()
    rd = wb.active
    rd.title = "Read me"
    lines = [
        (f"Chapter {chapter_no} Glossary Review: Thai and Simplified Chinese", True),
        (f"{course}, Chapter {chapter_no}, Lessons {lessons[0][0]}–{lessons[-1][0]}", False),
        ("", False),
        ("What this is", True),
        (f"All {len(terms)} glossary terms from the {len(lessons)} Chapter {chapter_no} lessons, in one place. The Thai and Chinese translations were machine-generated and have not yet been checked by a native speaker.", False),
        ("", False),
        ("What we ask", True),
        ("Thai-speaking colleague: please use the 'Thai review' sheet. Chinese-speaking colleague: please use the 'Chinese review' sheet.", False),
        ("For each row, choose a verdict in the 'Verdict' column: Correct, Change, or Unsure.", False),
        ("If you choose Change, write the better term in 'Suggested translation'. Add anything else in 'Comment'.", False),
        ("Rows shaded amber are the ones we are least sure about; the 'Check first' column says why. Please start with these.", False),
        ("", False),
        ("House conventions", True),
        ("Standard names and acronyms (for example RAM, CPU, ALU, NAND) and gate names (AND, OR, NOT, NAND, NOR, XOR) stay in Latin script, as in exam papers.", False),
        ("A term used in several lessons must have the same translation everywhere, so one correction here updates every lesson that uses it.", False),
        ("Definitions are in English only; they show the meaning the translation must match.", False),
        ("", False),
        ("Returning it", True),
        ("Please return the completed file to the class teacher. Corrections will be applied to every lesson glossary that uses the term.", False),
    ]
    for i, (text, bold) in enumerate(lines, 1):
        c = rd.cell(row=i, column=1, value=text)
        c.font = Font(name="Calibri", size=14 if i == 1 else 11, bold=bold, color=NAVY if bold else "000000")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    rd.column_dimensions["A"].width = 95
    rd.page_setup.fitToWidth, rd.page_setup.fitToHeight = 1, 0
    rd.sheet_properties.pageSetUpPr.fitToPage = True

    counts = {}
    for idx, (lang_short, lang_header) in enumerate(zip(LANG_NAMES, langs)):
        ws = wb.create_sheet(f"{lang_short} review")
        head = ["#", "Term", "English definition", "Lesson(s)", f"{LANG_LABEL[lang_short]} (machine translation)", "Check first",
                "Verdict", "Suggested translation", "Comment"]
        ws.append(head)
        for j in range(1, len(head) + 1):
            c = ws.cell(row=1, column=j)
            c.font = Font(name="Calibri", bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor=HDR)
            c.alignment = Alignment(wrap_text=True, vertical="center")
            c.border = border

        def why(k, v):
            reasons = [flags[lang_short][k]] if k in flags[lang_short] else []
            reasons += [r for text, r in contains.get(lang_short, {}).items() if text in v["tr"][idx]]
            return " ".join(reasons)

        items = list(terms.items())
        ordered = [(k, v) for k, v in items if why(k, v)] + [(k, v) for k, v in items if not why(k, v)]
        counts[lang_short] = sum(1 for k, v in items if why(k, v))
        for i, (k, v) in enumerate(ordered, 1):
            reason = why(k, v)
            ws.append([i, v["term"], v["definition"], ", ".join(f"L{n}" for n in v["lessons"]), v["tr"][idx], reason, "", "", ""])
            r = ws.max_row
            fill = FLAG if reason else (ALT if i % 2 == 0 else None)
            for j in range(1, len(head) + 1):
                c = ws.cell(row=r, column=j)
                c.alignment = wrap
                c.border = border
                c.font = Font(name="Calibri", size=11)
                if fill:
                    c.fill = PatternFill("solid", fgColor=fill)
        dv = DataValidation(type="list", formula1='"Correct,Change,Unsure"', allow_blank=True)
        dv.promptTitle, dv.prompt = "Verdict", "Correct, Change or Unsure"
        ws.add_data_validation(dv)
        dv.add(f"G2:G{ws.max_row}")
        for letter, w in zip("ABCDEFGHI", (5, 24, 48, 10, 26, 34, 12, 26, 30)):
            ws.column_dimensions[letter].width = w
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = f"A1:I{ws.max_row}"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "1:1"

    out = os.path.join(chapter, f"Chapter{chapter_no}_Glossary_Review.xlsx")
    wb.save(out)
    print(f"Glossary review: {out}")
    print(f"  {len(terms)} terms from Lessons {', '.join(str(n) for n, *_ in lessons)}; "
          f"check first: Thai {counts['Thai']}, Chinese {counts['Chinese']}")


if __name__ == "__main__":
    main(sys.argv[1])
