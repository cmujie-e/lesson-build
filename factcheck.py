"""List the checkable claims in a content.md that do NOT appear in the textbook chapter.

Usage: python factcheck.py <content.md> [chapter.pdf | chapter.txt]
The chapter defaults to the front-matter key `source_pdf:` (path relative to content.md, or absolute).

Claims looked for, in slides (text and notes), worksheet (questions, answers, marking) and
glossary definitions:
  - numbers with units          25 ns, 780 nm, 1.60 µm, 64 ms, 20 GB, 7,200 rpm, 80 %
  - larger or decimal numbers   1956, 3.75, 66,667
  - textbook references         Figure 3.6, Table 3.4, Activity 3A, Extension Activity 3B
  - quoted phrases (3+ words)   "tidying up the disk sectors"
Each one missing from the chapter is printed with where it is used. Lines that already say the
claim is not from the textbook (general knowledge, verified, correction, arithmetic, textbook
says ...) are marked DECLARED, so only UNDECLARED items need checking. This finds claims to
verify; it does not prove a found claim is used correctly.
"""
import os
import re
import shutil
import subprocess
import sys

from toolpaths import PDFTOTEXT  # poppler, not Git's xpdf copy (see toolpaths.py)
UNITS = r"(?:nm|µm|um|mm|cm|km|ms|µs|us|ns|s|kHz|MHz|GHz|Hz|TB|GB|MB|KB|kB|Kb|Mbit|bits?|bytes?|rpm|°C|%|dpi|ppi|kph|mph|V|W|mol)"
NUM_UNIT = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s?(" + UNITS + r")(?![\w])")
BIG_NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d{3,}|\d+\.\d+)(?![\w,]*\d)")
REFS = re.compile(r"\b((?:Extension )?Activity 3[A-H]|Figure 3\.\d+|Table 3\.\d+)\b")
QUOTE = re.compile(r"[\"“]([^\"”]{12,120})[\"”]")
DECLARED = re.compile(r"general knowledge|not textbook|not from the textbook|verified|correction|arithmetic|"
                      r"textbook says|textbook lists|textbook gives|textbook quotes|real-world|engagement|source: the jedec|"
                      r"illustrative|original scenario|credit|image:|photo:|syllabus", re.I)
SLIDE_DECLARED = re.compile(r"engagement (?:fact|callout)|not textbook content|verified against", re.I)


# the book writes units in full ("25 nanoseconds"); slides use abbreviations ("25 ns")
UNIT_WORDS = [(r"nanoseconds?", "ns"), (r"microseconds?", "µs"), (r"milliseconds?", "ms"), (r"seconds?", "s"),
              (r"nanomet(?:re|er)s?", "nm"), (r"micromet(?:re|er)s?", "µm"), (r"millimet(?:re|er)s?", "mm"),
              (r"centimet(?:re|er)s?", "cm"), (r"gigabytes?", "gb"), (r"megabytes?", "mb"), (r"kilobytes?", "kb"),
              (r"terabytes?", "tb"), (r"per cent|percent", "%"), (r"degrees? c(?:elsius)?", "°c")]
# numbers that are course or classroom policy, not textbook claims (course code, hingepoint threshold)
IGNORE = {"9618", "80%", "80 %"}


def expand_units(s):
    for pat, abbr in UNIT_WORDS:
        s = re.sub(r"(?<=\d)\s*" + pat + r"\b", " " + abbr, s, flags=re.I)
    return s


def norm(s):
    s = expand_units(s)
    s = s.replace("\u00ad", "").replace("μ", "µ").replace("−", "-").replace("–", "-").replace("’", "'")
    s = re.sub(r"(\d),(\d{3})", r"\1\2", s)          # 7,200 -> 7200
    s = re.sub(r"(\d)\s+(?=[a-zA-Zµ°%])", r"\1", s)   # 25 ns -> 25ns
    return re.sub(r"\s+", " ", s).lower()


def chapter_text(path):
    if path.lower().endswith(".pdf"):
        return subprocess.run([PDFTOTEXT, "-enc", "UTF-8", path, "-"], capture_output=True, text=True, encoding="utf-8").stdout
    return open(path, encoding="utf-8-sig").read()


def locations(text):
    """(location label, line) for every line worth checking."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    section, where = None, "?"
    for line in text.splitlines():
        if line.startswith("# "):
            section = line[2:].strip().upper()
            continue
        if section not in ("SLIDES", "WORKSHEET", "GLOSSARY"):
            continue
        m = re.match(r"^##\s+\w+\s*\|\s*(.+?)\s*\{#([a-z0-9-]+)\}", line)
        if m:
            where = f"slide {m.group(2)}"
            continue
        m = re.match(r"^###?\s+(\w+)\s*\|", line)
        if m and section == "WORKSHEET":
            where = f"worksheet {m.group(1)}"
            continue
        if re.match(r"^(image|credit|source|tag):", line):
            continue
        if section == "GLOSSARY" and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] != "Term":
                yield f"glossary {cells[0]}", cells[1]
            continue
        if line.strip():
            yield where, line


def main(content, source=None):
    text = open(content, encoding="utf-8-sig").read()
    if not source:
        m = re.search(r"^source_pdf:\s*(.+)$", text, re.M)
        if not m:
            sys.exit("No chapter given and no source_pdf: in the front matter")
        source = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(content)), m.group(1).strip()))
    book = norm(chapter_text(source))
    found, missing = 0, []
    lines = list(locations(text))
    # a slide whose notes declare it a verified engagement fact: all its claims count as declared
    declared_where = {w for w, l in lines if SLIDE_DECLARED.search(l)}
    for where, line in lines:
        claims = [m.group(0) for m in NUM_UNIT.finditer(line)]
        claims += [m.group(1) for m in BIG_NUM.finditer(line) if not any(m.group(1) in c for c in claims)]
        claims += [m.group(1) for m in REFS.finditer(line)]
        # quotes are claims only when attributed to the book; other quotes are our own prompts
        if re.search(r"\btextbook\b|\bthe book\b", line, re.I):
            claims += [m.group(1) for m in QUOTE.finditer(line) if len(m.group(1).split()) >= 3]
        for c in dict.fromkeys(claims):
            if c.strip() in IGNORE:
                continue
            if norm(c) in book:
                found += 1
            else:
                missing.append((where, c, bool(DECLARED.search(line)) or where in declared_where, line.strip()))
    undeclared = [m for m in missing if not m[2]]
    print(f"Chapter: {os.path.basename(source)}")
    print(f"{found} claims found in the chapter; {len(missing)} not found "
          f"({len(missing) - len(undeclared)} declared as non-textbook, {len(undeclared)} undeclared).\n")
    for label, items in (("UNDECLARED: check these", undeclared), ("DECLARED (the line says it is not from the textbook)",
                                                                   [m for m in missing if m[2]])):
        if items:
            print(label)
            for where, c, _, line in items:
                print(f"  {where:<26} {c!r:<28} {line[:90]}")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
