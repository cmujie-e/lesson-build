---
lesson: N
chapter: N
topic: Lesson Topic In Title Case
deck_name: LessonN_Lesson_Topic
prefix: LessonN
footer: 9618 AS Level CS • ChN LN • Lesson Topic
source: textbook name and section this lesson is written from
---

<!--
CONTENT TEMPLATE. Copy to <lesson folder>\content.md, fill in, then:
  python lesson.py draft <content.md>    check word counts etc. before images are downloaded
  python commons.py fetch <content.md>   list Commons images still to download (add --yes after approval)
  python lesson.py build <content.md>    build the deliverables into the lesson folder and check them
Rules (word limit, font size, which documents) come from the nearest course.json above this file.

SLIDES   "## <layout> | <title> {#id}"      ids: lowercase letters, digits, hyphens; unique
  layouts: title    subtitle: line
           bullets  optional plain lead line(s), then "- " bullets
           text     plain lines (questions, numbered lines "1. ...")
           cards    "- Heading :: detail" (2-4 cards), optional plain line under them
           table    "| a | b |" rows; first row is the header
           image    bullets and/or plain lines + image: / credit: (/ source:)
  keys (before the body): tag: (e.g. DO NOW, CFU, STOP & CHECK, ANSWER, EXIT TICKET)
                          image: assets/file.jpg   credit: full credit line (required with image)
                          source: commons File:Name.jpg   (Commons images only; used by commons.py)
  "notes:" starts the speaker notes, which run to the next "## " or "# " heading.
  Question slides (tags listed in course.json) need "Answer: ..." in their notes and an
  answer slide straight after. "@id" anywhere becomes that slide's number.
  An "Image credits" slide is added automatically when any slide has an image.

WORKSHEET  "## <letter> | <section name>", optional lines: wordbank:, reference: <title>,
  a "|" table (reference data), image: + credit: (+ source:), plain instruction lines.
  Then "### <item> | <marks>", question text, answer:, marking:, lines: (answer lines, optional).
  Section and worksheet totals are added up automatically.

LESSON PLAN / ASSESSMENT PLAN  "## Heading" sections holding paragraphs, "- " bullets or "|" tables.
  The lesson plan needs a "## Timing" table: | Start | End | Min | Phase | Activity | Slides |
  (Min must add up to lesson_minutes; a phase containing "Practice" must meet min_practice_minutes).
  Put {{worksheet_answer_key}} on its own line in the assessment plan where the key should go.

GLOSSARY  one "|" table: Term | English definition | Thai | Chinese Simplified (or your languages).
GLOSSARY NOTES  plain lines; the first line is the sheet heading.
-->

# SLIDES

## title | Lesson Topic In Title Case {#title}
subtitle: Chapter N · Lesson N · Course name
notes:
Source: textbook section and pages.
Say: opening script.

## text | Do Now – Retrieval Practice {#donow}
tag: DO NOW
1. Retrieval question from an earlier lesson?
2. Retrieval question?
notes:
Answer: 1. ... 2. ...

## text | Do Now – Answers {#donow-a}
tag: ANSWERS
1. Short answer.
2. Short answer.
notes:
Answer: see slide.

## bullets | Learning Objectives {#lo}
tag: OBJECTIVES
By the end, you can:
- Objective one.
- Objective two.
notes:
Source: syllabus reference.

## image | Concept Slide With A Picture {#concept1}
tag: CONCEPT
image: assets/example.jpg
credit: "Example.jpg" by Author, Wikimedia Commons, CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:Example.jpg
source: commons File:Example.jpg
- Short point
- Short point
notes:
Source: textbook section.
Say: explanation.

## text | Check for Understanding {#cfu1}
tag: CFU
Question?
notes:
Answer: full answer.
Decision rule: what to do if most students miss it (e.g. re-show slide @concept1).

## bullets | CFU – Answer {#cfu1-a}
tag: ANSWER
- Short answer
notes:
Answer: as shown.

## text | Exit Ticket {#exit}
tag: EXIT TICKET
1. Question. [1]
notes:
Answer: 1. ...

## text | Exit Ticket – Answers {#exit-a}
tag: ANSWERS
1. Short answer.
notes:
Answer: as shown.

# WORKSHEET

intro: Instructions for students.

## A | Section name

### A1 | 2
Question text.
answer: Accepted answer (1); second point (1).
marking: How to award the marks.
lines: 3

# MARK SCHEME

note: Marking approach for the whole worksheet.

# LESSON PLAN

## Lesson overview
- Course, chapter, lesson, duration, source.

## Learning objectives
- Objective one.

## Success criteria
- Criterion one.

## Timing
| Start | End | Min | Phase | Activity | Slides |
| 0 | 5 | 5 | Do Now | Retrieval | @title–@donow-a |
| 5 | 58 | 53 | Teach | Concepts and checks | @lo–@cfu1-a |
| 58 | 70 | 12 | Practice | Worksheet | @exit–@exit-a |

## Homework
- Homework task.

# ASSESSMENT PLAN

## Assessment objectives
| Objective | Where assessed | AO |
| Objective one | CFU 1; Worksheet A | AO1 |

{{worksheet_answer_key}}

## Grade descriptors
| Level | Worksheet | Description |
| Secure | 80%+ | ... |

# GLOSSARY

| Term | English definition | Thai (ไทย) | Chinese Simplified (简体中文) |
| Term | Definition. | คำ | 术语 |

# GLOSSARY NOTES

Translation accuracy notice
Machine-generated translations must be checked before use.
