---
chapter: N
title: Chapter Title In Title Case
prefix: ChN_Unit_MCQ
minutes: 30
lessons: 8
source: textbook name and chapter the questions are written from
---

<!--
UNIT MCQ TEMPLATE. One per chapter: copy to <chapter folder>\Unit_MCQ\mcq.md, fill in, then:
  python lesson.py mcq <mcq.md>     build the question paper and answer key into this folder and check them
Rules (question count, options per question, answer balance, file names) come from the
"unit_mcq" block of the nearest course.json above this file.
Draw on each lesson's assessment plan "Feeding Forward" section for candidate questions.

FRONT MATTER  chapter, title, prefix (file name stem), minutes (time allowed, printed on the paper),
  lessons (how many lessons the chapter has: every lesson 1..N needs at least one question), source.

INSTRUCTIONS  optional plain lines printed under the standard instructions on the paper.

QUESTIONS  "## <number> | L<lesson> | AO<n>", numbered 1, 2, 3 ... in order. Then, in this order:
  question text (plain lines; joined into one paragraph)
  optional "|" table (first row is the header), e.g. a truth table
  optional image: assets/file.png + credit: full credit line (+ width: <cm>), printed under the question
  the options, one per line: "A. ...", "B. ...", "C. ...", "D. ..."
  answer: <letter>
  why <letter>: why each WRONG option is wrong (one line per wrong option; the misconception it tests)
  source: textbook section/page the question is checked against (answer key only)
  Every question needs every option, one correct letter and a "why" for each wrong option.
  The paper never shows answer:, why or source: lines; they go to the answer key only.
-->

# INSTRUCTIONS

Optional extra instruction for this paper.

# QUESTIONS

## 1 | L1 | AO1
Question stem?
A. First option
B. Second option
C. Third option
D. Fourth option
answer: B
why A: the misconception this distractor tests
why C: the misconception this distractor tests
why D: the misconception this distractor tests
source: textbook section and page

## 2 | L2 | AO2
Question stem that refers to the table below?
| Input A | Input B | Output |
| 0 | 0 | 1 |
| 1 | 1 | 0 |
image: assets/example.png
credit: full credit line for the image
A. First option
B. Second option
C. Third option
D. Fourth option
answer: D
why A: reason
why B: reason
why C: reason
source: textbook section and page
