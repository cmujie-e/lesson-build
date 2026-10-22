"""Google Forms version of a chapter's unit MCQ: writes an Apps Script that builds the quiz.

Usage: python make_form.py <mcq.md>        (run by `lesson.py form`)

Reads mcq.md through parse_mcq.py, so the form carries exactly the paper's questions, options,
correct letters and wrong-option reasons. Writes <prefix>_Form.gs next to mcq.md.
Images: a question's own image (assets/...) is used as it is; a question with a table (Forms cannot
show tables) gets the table drawn as assets/qNN_table.png in the house style. The script reads the
images from Google Drive at <chapter folder>/Unit_MCQ/assets, so mcq.md must sit in
<chapter folder>/Unit_MCQ and the chapter folder must be synced to Drive.
The teacher runs the script once from script.google.com; instructions are in the script header.
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY, INK, AMBER, LIGHT, GRID = (0x3A, 0x44, 0x88), (0x1E, 0x27, 0x61), (0xFF, 0xC8, 0x57), (0xF4, 0xF6, 0xFC), (0xCA, 0xDC, 0xFC)


def table_image(rows, path):
    """House-style table image (navy header; amber for a leading 'Row' column), as on the slides."""
    font = ImageFont.truetype(r"C:\Windows\Fonts\calibri.ttf", 64)
    bold = ImageFont.truetype(r"C:\Windows\Fonts\calibrib.ttf", 64)
    head, body = rows[0], rows[1:]
    cw = [max(150, 40 + max(int(bold.getlength(str(r[j]))) for r in rows)) for j in range(len(head))]
    rh = 92
    W, H = sum(cw), rh * len(rows)
    im = Image.new("RGB", (W + 2, H + 2), "white")
    d = ImageDraw.Draw(im)
    xs = [sum(cw[:j]) for j in range(len(cw) + 1)]
    for j, c in enumerate(head):
        amber = j == 0 and c.lower() == "row"
        d.rectangle([xs[j], 0, xs[j + 1], rh], fill=AMBER if amber else NAVY)
        d.text(((xs[j] + xs[j + 1]) / 2, rh / 2), str(c), font=bold, fill=INK if amber else "white", anchor="mm")
    for i, r in enumerate(body, 1):
        d.rectangle([0, i * rh, W, (i + 1) * rh], fill=LIGHT if i % 2 == 0 else (255, 255, 255))
        for j, v in enumerate(r):
            d.text(((xs[j] + xs[j + 1]) / 2, i * rh + rh / 2), str(v), font=bold if j == len(r) - 1 else font, fill=INK, anchor="mm")
    for x in xs:
        d.line([x, 0, x, H], fill=GRID, width=3)
    for i in range(len(rows) + 1):
        d.line([0, i * rh, W, i * rh], fill=GRID, width=3)
    d.line([xs[-2], 0, xs[-2], H], fill=NAVY, width=7)  # rule before the output column
    im.save(path)


def main(src):
    src = os.path.abspath(src)
    unit = os.path.dirname(src)
    chapter_dir = os.path.dirname(unit)
    if os.path.basename(unit) != "Unit_MCQ":
        sys.exit(f"mcq.md must be in <chapter folder>\\Unit_MCQ (found {unit})")
    tmp = os.path.join(HERE, "out", "form_" + os.path.basename(chapter_dir).replace(" ", ""), "mcq.json")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    subprocess.run([sys.executable, "parse_mcq.py", src, tmp], cwd=HERE, check=True, capture_output=True)
    M = json.load(open(tmp, encoding="utf-8"))
    assets = os.path.join(unit, "assets")
    os.makedirs(assets, exist_ok=True)

    questions = []
    for q in M["questions"]:
        text = " ".join(q["text"]) if isinstance(q["text"], list) else q["text"]
        if q.get("image"):
            image = os.path.basename(q["image"])
        elif q.get("table"):
            image = f"q{q['number']:02d}_table.png"
            table_image(q["table"], os.path.join(assets, image))
        else:
            image = None
        if image and not os.path.exists(os.path.join(assets, image)):
            sys.exit(f"Question {q['number']}: image not found in {assets}: {image}")
        wrong = " ".join(f"{L}: {why.rstrip('.')}." for L, why in sorted(q["why"].items()))
        questions.append({
            "n": q["number"], "lesson": q["lesson"], "text": text, "image": image,
            "options": [f"{o['letter']}. {o['text']}" for o in q["options"]],
            "answer": [o["letter"] for o in q["options"]].index(q["answer"]),
            "feedback": f"Correct answer: {q['answer']}. Why the others are wrong: {wrong}",
        })

    meta = M["meta"]
    title = f"Chapter {meta['chapter']} Unit Test: {meta['title']}"
    n = len(questions)
    data = json.dumps(questions, ensure_ascii=False, indent=1)
    image_path = json.dumps([os.path.basename(chapter_dir), "Unit_MCQ", "assets"], ensure_ascii=False)
    images = ", ".join(sorted({q["image"] for q in questions if q["image"]})) or "none"
    out = os.path.join(unit, f"{meta['prefix']}_Form.gs")
    script = f"""/**
 * {title}: builds a Google Forms quiz with the {n} questions of the paper version
 * (Unit_MCQ\\{meta['prefix']}.pdf). {M['config'].get('course', '')}.
 *
 * GENERATED from Unit_MCQ\\mcq.md by lesson-build (python lesson.py form). Do not edit the questions
 * here: change mcq.md, rebuild the paper (python lesson.py mcq) and regenerate this file.
 * Questions, options, correct answers and marks are identical to the paper and answer key.
 *
 * HOW TO RUN (about 3 minutes)
 * 1. Go to https://script.google.com and click "New project".
 * 2. Delete the sample code, paste this whole file in, and click Save.
 * 3. Choose createUnitTest in the function menu and click Run.
 * 4. The first time, Google asks you to authorise the script. It needs permission to create a form and
 *    to READ image files in your Drive ({' > '.join(json.loads(image_path))}: {images}).
 *    Click Review permissions, choose your school account, then Allow.
 * 5. Open the Execution log. It prints two links:
 *      - EDIT link: open it to check the quiz (each question's correct answer and feedback are set).
 *      - STUDENT link: attach the form in Google Classroom (Add > Google Forms).
 * 6. IMPORTANT, before posting: in the form open Settings > Quizzes and set
 *      Release grades: "Later, after manual review"
 *    and switch OFF "Missed questions", "Correct answers" and "Point values" under Respondent settings.
 *    Apps Script cannot change these. If you skip this, a student who finishes first could see the answers
 *    and pass them on. Switch them back on after everyone has sat the test, then Release scores.
 * 7. Forms has no timer: the {meta['minutes']}-minute limit is printed in the description; keep time in the room.
 *
 * MARKING: every question is multiple choice with its correct answer set, so Forms marks it automatically
 * (1 mark each, {n} marks). The feedback on each question gives the reason each wrong option is wrong,
 * taken from the answer key; students see it only when you release it.
 */

const FORM_TITLE = {json.dumps(title, ensure_ascii=False)};
const MINUTES = {meta['minutes']};
const FOLDER_ID = ''; // optional: Drive folder ID to save the form in (e.g. the Unit_MCQ folder)
const IMAGE_PATH = {image_path}; // where the question images are in Drive

const QUESTIONS = {data};

function createUnitTest() {{
  const form = FormApp.create(FORM_TITLE);
  const needsImages = QUESTIONS.some(function (q) {{ return q.image; }});
  const images = needsImages ? findImageFolder_() : null;
  form.setIsQuiz(true)
    .setDescription(
      'Time allowed: ' + MINUTES + ' minutes. Answer all ' + QUESTIONS.length + ' questions. ' +
      'Each question has exactly one correct answer and is worth 1 mark. ' +
      'Closed book: no notes, slides, textbook or help.')
    .setCollectEmail(true)
    .setLimitOneResponsePerUser(true) // students must be signed in to their school account
    .setAllowResponseEdits(false)
    .setShowLinkToRespondAgain(false)
    .setPublishingSummary(false)
    .setShuffleQuestions(false)
    .setConfirmationMessage('Your answers have been recorded. Your teacher will release your score.');

  form.addCheckboxItem()
    .setTitle('I am answering alone, without notes, slides, the textbook or help.')
    .setChoiceValues(['I confirm'])
    .setRequired(true);

  QUESTIONS.forEach(function (q) {{
    if (q.image) {{
      form.addImageItem()
        .setTitle('Question ' + q.n)
        .setImage(imageBlob_(images, q.image))
        .setAlignment(FormApp.Alignment.CENTER);
    }}
    const item = form.addMultipleChoiceItem();
    item.setTitle(q.n + '. ' + q.text)
      .setChoices(q.options.map(function (text, i) {{ return item.createChoice(text, i === q.answer); }}))
      .setPoints(1)
      .setRequired(true)
      .setFeedbackForCorrect(FormApp.createFeedback().setText('Correct.').build())
      .setFeedbackForIncorrect(FormApp.createFeedback().setText(q.feedback).build());
  }});

  if (FOLDER_ID) {{
    DriveApp.getFileById(form.getId()).moveTo(DriveApp.getFolderById(FOLDER_ID));
  }}
  Logger.log('Questions added: ' + QUESTIONS.length);
  Logger.log('EDIT link (teacher only): ' + form.getEditUrl());
  Logger.log('STUDENT link: ' + form.getPublishedUrl());
}}

/** Walks the folders in IMAGE_PATH (the first match of each name). */
function findImageFolder_() {{
  const top = DriveApp.getFoldersByName(IMAGE_PATH[0]);
  if (!top.hasNext()) throw new Error('Folder not found in Drive: ' + IMAGE_PATH[0]);
  let folder = top.next();
  for (let i = 1; i < IMAGE_PATH.length; i++) {{
    const next = folder.getFoldersByName(IMAGE_PATH[i]);
    if (!next.hasNext()) throw new Error('Folder not found: ' + IMAGE_PATH.slice(0, i + 1).join(' > '));
    folder = next.next();
  }}
  return folder;
}}

function imageBlob_(folder, name) {{
  const files = folder.getFilesByName(name);
  if (!files.hasNext()) throw new Error('Image not found in ' + IMAGE_PATH.join(' > ') + ': ' + name);
  return files.next().getBlob();
}}
"""
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(script)
    print(f"Form script: {out}")
    print(f"  {n} questions; answers {''.join(q['options'][q['answer']][0] for q in questions)}; images: {images}")


if __name__ == "__main__":
    main(sys.argv[1])
