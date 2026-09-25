"""Layout checks on the rendered PDFs, for problems found by eye in earlier builds.

Usage: python check_layout.py <lesson.json> <deck.pdf> <doc.pdf> [<doc.pdf> ...]
(lesson.py runs this after rendering; the PDFs are the deck and every document as rendered.)

  1. Slide text overflow    words below the content area or past the right edge of a slide
                            (text running out of its box collides with the footer)
  2. Near-empty pages       a document page after the first holding under 3 lines of text
                            (e.g. a credits line or one heading pushed onto its own page)
  3. Stranded headings      a page whose last line is a section heading (its content starts overleaf)
  4. Mid-word breaks        a word split across two lines, e.g. "Developme" / "nt" in a narrow table cell
These catch known failure patterns; they do not replace looking at the inspection sheets.
"""
import html
import json
import re
import shutil
import subprocess
import sys

from toolpaths import PDFTOTEXT  # poppler, not Git's xpdf copy (see toolpaths.py)
WORD = re.compile(r"[A-Za-z]+")


def pages_text(pdf):
    out = subprocess.run([PDFTOTEXT, "-enc", "UTF-8", pdf, "-"], capture_output=True, text=True, encoding="utf-8").stdout
    return [[l.strip() for l in p.splitlines() if l.strip()] for p in out.split("\f")][:-1] or [[]]


def words_bbox(pdf):
    """[(page_no, page_w, page_h, [(xMin, yMin, xMax, yMax, word), ...]), ...]"""
    out = subprocess.run([PDFTOTEXT, "-bbox", "-enc", "UTF-8", pdf, "-"], capture_output=True, text=True, encoding="utf-8").stdout
    pages = []
    for i, m in enumerate(re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', out, re.S), 1):
        words = [(float(a), float(b), float(c), float(d), html.unescape(w)) for a, b, c, d, w in
                 re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', m.group(3))]
        pages.append((i, float(m.group(1)), float(m.group(2)), words))
    return pages


def vocabulary(L):
    text = json.dumps(L, ensure_ascii=False)
    return {w.lower() for w in WORD.findall(text)}


def slide_overflow(deck_pdf, L):
    """Content must end above 6.95 in (the footer sits at 7.15 in) on a 7.5 in tall slide."""
    footer_words = set(L["meta"].get("footer", "").split())  # whole tokens: "Ch3", "L2", "•"
    problems = []
    for n, w, h, words in words_bbox(deck_pdf):
        bottom, footer_top = h * 6.97 / 7.5, h * 7.12 / 7.5
        for x0, y0, x1, y1, word in words:
            in_footer_band = y0 >= footer_top and (word in footer_words or word.isdigit() or not WORD.search(word))
            if (y1 > bottom and not in_footer_band) or x1 > w - 2:
                problems.append(f"slide {n}: text outside the content area near \"{word}\"")
                break
    return problems


def near_empty(pdf, name):
    return [f"{name} page {i}: only {len(p)} line(s) of text" for i, p in enumerate(pages_text(pdf), 1)
            if i > 1 and len(p) < 3]


def stranded(pdf, name, headings):
    probs = []
    pages = pages_text(pdf)
    for i, p in enumerate(pages[:-1], 1):
        last = p[-1] if p else ""
        if any(last.startswith(h) for h in headings):
            probs.append(f"{name} page {i}: ends with heading \"{last[:50]}\"")
    return probs


def midword(pdf, name, vocab):
    probs = []
    for i, p in enumerate(pages_text(pdf), 1):
        for a, b in zip(p, p[1:]):
            wa, wb = WORD.findall(a), WORD.findall(b)
            if not wa or not wb or a.endswith("-") or not b[0].isalpha() or b[0].isupper():
                continue
            x, y = wa[-1], wb[0]
            if not a.endswith(x):
                continue
            joined = (x + y).lower()
            if len(x) >= 3 and joined in vocab and x.lower() not in vocab and y.lower() not in vocab:
                probs.append(f"{name} page {i}: \"{x}\" / \"{y}\" looks like a word split across lines")
    return probs


def headings_of(L):
    hs = [f"Section {s['letter']}:" for s in L["worksheet"]["sections"]]
    hs += [s["heading"] for s in L["lesson_plan"] + L["assessment_plan"] if s.get("heading")]
    hs += [f"Slide {i} ·" for i in range(1, len(L["slides"]) + 1)]
    return [h for h in hs if h]


def main(lj, deck, *docs):
    L = json.load(open(lj, encoding="utf-8"))
    vocab, heads = vocabulary(L), headings_of(L)
    problems = slide_overflow(deck, L) if deck != "-" else []
    problems += midword(deck, "deck", vocab) if deck != "-" else []
    for d in docs:
        # "sheet:" marks a spreadsheet PDF: each sheet starts a new page by design, so no near-empty check
        sheet = d.startswith("sheet:")
        d = d[6:] if sheet else d
        name = re.sub(r"\.pdf$", "", d.replace("\\", "/").split("/")[-1])
        problems += ([] if sheet else near_empty(d, name)) + stranded(d, name, heads) + midword(d, name, vocab)
    for p in problems:
        print(f"[FAIL] {p}")
    print(f"Layout checks: {len(problems)} problem(s) in {1 + len(docs)} files")
    print("RESULT:", "PASS" if not problems else "FAIL")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
