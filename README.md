# lesson-build

Builds a complete, checked lesson resource bundle from one text file (`content.md`):
slide deck with speaker notes, bilingual glossary, worksheet, mark scheme, lesson plan and
assessment plan. Which documents a course needs, and its slide rules, come from a
`course.json` file, so the same tool serves different grades and courses.

The scripts build and check; they do not write lesson content. Writing `content.md`
(from the textbook, with facts checked) is the teacher's or Claude's job.

## One-time setup on a new PC

1. Install **Node.js**, **Python 3**, **LibreOffice** and **Git**.
2. Download poppler for Windows (the `Release-*.zip` from
   https://github.com/oschwartz10612/poppler-windows/releases), extract it (e.g. to `C:\poppler`)
   and add its `Library\bin` folder and `C:\Program Files\LibreOffice\program` to your user PATH.
3. In this folder:
   ```
   npm install
   python -m pip install python-pptx openpyxl "markitdown[pptx,docx,xlsx]" pillow
   ```

## Building a lesson

```
python lesson.py draft  "<lesson folder>\content.md"   # check before images are downloaded
python commons.py fetch "<lesson folder>\content.md"   # list Commons images still to download
python commons.py fetch "<lesson folder>\content.md" --yes   # download them
python lesson.py build  "<lesson folder>\content.md"   # build into the lesson folder + all checks
```

`build` writes the deliverables next to `content.md` (or to a folder given as a third
argument), then runs the slide check and the bundle check and writes contact sheets of every
page to `out\<lesson>\qa` for visual inspection. It stops at the first failure, and refuses to
run while a deliverable is open in Office. `draft` does the same into `out\` only.

Start a new lesson from `templates\content_template.md`; its comment block documents the format.

## Finding images

```
python commons.py search "laser printer drum"
python commons.py category "Category:Laser printers"
python commons.py info "File:Some_image.jpg"     # prints credit: and source: lines to paste
python textbook_figure.py <pdf> <page> <x0> <y0> <x1> <y1> <out.png> 600   # crop a textbook figure
```
Textbook figure boxes are in points, read off a `pdftoppm -r 72` render of the page.
Only use textbook images where the school holds a licence for the book.

## Rules for a course: course.json

Put a `course.json` in the lesson folder or any folder above it (the nearest one wins, so one
file can cover a whole chapter or course). `courses\9618_chapter3.json` is the Grade 11
Chapter 3 version; copy it as a starting point. Fields:

| Field | Meaning |
|---|---|
| `course` | Course name printed on documents |
| `lesson_minutes`, `min_practice_minutes` | Checked against the lesson plan's Timing table |
| `slides.max_words`, `slides.body_pt` | Word limit (title excluded) and text size on slides |
| `slides.chrome_pt` | Footer, page number and tag sizes (exempt from the rules above) |
| `slides.question_tags`, `answer_marker` | Slides that must have an answer in their notes |
| `slides.tag_colors`, `box_colors` | Palette names from `lib\style.js` |
| `documents` | The deliverables: `type` (deck, speaker_notes, glossary, worksheet, mark_scheme, lesson_plan, assessment_plan) and `file` name pattern using `{prefix}` / `{deck_name}`; `.pdf` names are converted from Word |

Document types not listed above (for example a submission sheet) are not built yet;
`lesson.py` stops with a clear message if a course asks for one.

## Files

| File | Job |
|---|---|
| `lesson.py` | One command: build, check, render |
| `parse_content.py` | content.md -> lesson.json (resolves `@slide` references, images, credits) |
| `build_deck.js` | Slide deck (pptxgenjs) |
| `build_docs.js` | Speaker notes, worksheet, mark scheme, lesson plan, assessment plan (docx) |
| `build_glossary.py` | Glossary workbook (openpyxl) |
| `check_deck.py` | Per-slide rules: words, font size, notes, answers, image credits |
| `check_bundle.py` | Files present, answer keys match, marks add up, timing, placeholders |
| `commons.py` | Wikimedia Commons search, credits and paced downloads |
| `textbook_figure.py` | Crop a figure from a textbook PDF at print resolution |
| `snapshot.py` | Text snapshot of a built lesson, for regression tests |
| `montage.py` | Contact sheets of rendered pages |
| `lib\` | House style: colours, slide chrome, Word helpers, icons |

Images are never committed: they live in each lesson's `assets` folder.
