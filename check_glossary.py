"""Cross-lesson glossary check: a term must have the same translations in every lesson.

Usage: python check_glossary.py <content.md>
Compares this lesson's GLOSSARY table with every other content.md under the folder holding the
course.json that governs this lesson (so a chapter-level course.json compares the whole chapter).
Terms match on their name, ignoring case and any bracketed part: "EEPROM (Electrically
Erasable PROM)" and "EEPROM" are the same term. Folders named out or _duplicates are skipped.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_content import find_config, split_sections  # noqa: E402


def glossary(path):
    with open(path, encoding="utf-8-sig") as f:
        _, sections = split_sections(f.read())
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in sections.get("GLOSSARY", []) if l.lstrip().startswith("|")]
    return {key(r[0]): r for r in rows[1:] if r and r[0]}


def key(term):
    return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", term)).strip().lower()


def main(content):
    content = os.path.abspath(content)
    with open(content, encoding="utf-8-sig") as f:
        front, _ = split_sections(f.read())
    root = os.path.dirname(find_config(content, front))
    others = [p for p in glob.glob(os.path.join(root, "**", "content.md"), recursive=True)
              if os.path.abspath(p) != content and not re.search(r"[\\/](out|_duplicates)[\\/]", p)]
    mine = glossary(content)
    problems, shared = [], 0
    for other in sorted(others):
        theirs = glossary(other)
        for k, row in mine.items():
            if k in theirs:
                shared += 1
                for col, lang in ((2, "Thai"), (3, "Chinese")):
                    a = row[col] if len(row) > col else ""
                    b = theirs[k][col] if len(theirs[k]) > col else ""
                    if a != b:
                        rel = os.path.relpath(other, root)
                        problems.append(f"\"{row[0]}\" {lang}: {a!r} here vs {b!r} in {rel}")
    for p in problems:
        print(f"[FAIL] {p}")
    print(f"Glossary: {len(mine)} terms; {shared} shared with {len(others)} other lesson(s); {len(problems)} mismatch(es)")
    print("RESULT:", "PASS" if not problems else "FAIL")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
