/**
 * Build the lesson's Word documents from lesson.json (output of parse_content.py).
 * Usage: node build_docs.js <lesson.json> <out_dir>
 *
 * Writes: <prefix>_Speaker_Notes.docx, <prefix>_Worksheet.docx (both converted to PDF later),
 *         <prefix>_Mark_Scheme.docx, <prefix>_Lesson_Plan.docx, <prefix>_Assessment_Plan.docx
 * Mark scheme and assessment plan answer keys both come from the same worksheet data,
 * so their answers and marks cannot drift apart.
 */
const fs = require('fs');
const path = require('path');
const { Paragraph, TextRun, TabStopType } = require('docx');
const H = require('./lib/docx_helpers');

const { gap, para, bullet, heading, save } = H;

/** "Label: text" lines get a bold label, used in the speaker notes. */
function labelled(line) {
  const m = line.match(/^([A-Z][A-Za-z ()]{1,30}):\s+(.*)$/);
  if (!m) return para(line);
  return new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: `${m[1]}: `, bold: true, size: 21 }), new TextRun({ text: m[2], size: 21 })] });
}

function header(meta, docTitle) {
  return [
    H.banner(`${docTitle}`, { size: 30 }),
    para(`${meta.course} · Chapter ${meta.chapter} · Lesson ${meta.lesson}: ${meta.topic}`, { color: H.NAVY, p: { spacing: { before: 100, after: 200 } } }),
  ];
}

function blocksToDocx(blocks) {
  const out = [];
  for (const b of blocks) {
    if (b.type === 'para') out.push(para(b.text));
    else if (b.type === 'bullets') b.items.forEach((t) => out.push(bullet(t)));
    else if (b.type === 'table') { out.push(H.itemTable(b.rows[0], b.rows.slice(1))); out.push(gap(120)); }
  }
  return out;
}

function sectionsToDocx(sections, placeholders = {}) {
  const out = [];
  sections.forEach((s, i) => {
    const ph = s.blocks.find((b) => b.type === 'placeholder');
    if (ph) { out.push(...placeholders[ph.name]()); return; }
    if (s.heading) out.push(heading(s.heading));
    out.push(...blocksToDocx(s.blocks));
    // no spacer after the last section: when a page is full it spills onto a blank page
    if (i < sections.length - 1) out.push(gap(200));
  });
  return out;
}

// ---------- Speaker notes ----------
function speakerNotes(L) {
  const out = header(L.meta, `Lesson ${L.meta.lesson} Speaker Notes: ${L.meta.topic}`);
  out.push(para(`Extracted from the notes fields of ${L.meta.deck_name}.pptx. Every question slide's notes include its answer.`, { italics: true }));
  L.slides.forEach((s, i) => {
    out.push(heading(`Slide ${i + 1} · ${s.title}${s.tag ? `  [${s.tag}]` : ''}`));
    s.notes.split('\n').filter((l) => l.trim()).forEach((l) => out.push(labelled(l.trim())));
  });
  return out;
}

// ---------- Worksheet (student-facing, no answers) ----------
/**
 * Answer lines drawn as an underscore tab leader, one paragraph per line. (Stacked paragraphs
 * with identical bottom borders merge into a single bordered block and show only one line.)
 * keepNext on all but the last line keeps a question's writing space on one page.
 */
function answerLines(n) {
  return [...Array(n)].map((_, i) => new Paragraph({
    spacing: { before: 170, after: 0 }, keepNext: i < n - 1,
    tabStops: [{ type: TabStopType.RIGHT, position: 9690, leader: 'underscore' }],
    children: [new TextRun({ text: '\t', size: 21, color: '9AA3C7' })],
  }));
}

function worksheet(L) {
  const W = L.worksheet;
  const out = header(L.meta, `Lesson ${L.meta.lesson} Worksheet: ${L.meta.topic}`);
  out.push(H.nameRow(W.total), gap(120), para(W.intro, { italics: true }), gap(120));
  for (const sec of W.sections) {
    out.push(heading(`Section ${sec.letter}: ${sec.name}   ·   ${sec.marks} mark${sec.marks === 1 ? '' : 's'}`));
    if (sec.wordbank) out.push(H.noteBox(`Word bank:  ${sec.wordbank}`, { size: 22 }), gap(80));
    sec.instructions.forEach((t) => out.push(para(t, { italics: true, p: { keepNext: true } })));
    // a section image comes before its reference table (e.g. a circuit, then the table to complete for it)
    if (sec.image) out.push(H.docImage(sec, sec.reference_title || 'Reference diagram'));
    if (sec.reference_title) out.push(para(sec.reference_title, { bold: true, color: H.NAVY, p: { keepNext: true } }));
    if (sec.reference.length) out.push(H.itemTable(sec.reference[0], sec.reference.slice(1), { keepTogether: true }), gap(120));
    for (const q of sec.questions) {
      out.push(new Paragraph({
        spacing: { before: 200, after: 40 }, keepNext: true,
        tabStops: [{ type: TabStopType.RIGHT, position: 9600 }],
        children: [
          new TextRun({ text: `${q.item}   `, bold: true, size: 21, color: H.NAVY }),
          new TextRun({ text: q.text, size: 21 }),
          new TextRun({ text: `\t[${q.marks}]`, bold: true, size: 21 }),
        ],
      }));
      if (q.image) out.push(H.docImage(q, `Diagram for ${q.item}`, 80));
      out.push(...answerLines(q.lines));
    }
    if (sec !== W.sections[W.sections.length - 1]) out.push(gap(240));
  }
  if (W.credits && W.credits.length) {
    out.push(para(`Image credits. ${W.credits.join(' ')}`, { size: 15, italics: true, color: '555555', p: { spacing: { before: 120, after: 0 } } }));
  }
  return out;
}

// ---------- Mark scheme (compact) ----------
function markScheme(L) {
  const W = L.worksheet;
  const out = header(L.meta, `Lesson ${L.meta.lesson} Mark Scheme: ${L.meta.topic}`);
  out.push(H.noteBox(`Marking approach: ${L.mark_scheme_note}`), gap(160));
  let running = 0;
  for (const sec of W.sections) {
    running += sec.marks;
    out.push(heading(`Section ${sec.letter}: ${sec.name} (${sec.marks} marks)   ·   running total ${running} / ${W.total}`));
    out.push(H.itemTable(['Item', 'Accepted answer', 'Marks'], sec.questions.map((q) => [q.item, q.answer, q.marks]), { widths: [9, 80, 11] }));
    out.push(gap(120));
  }
  const sum = W.sections.map((s) => s.marks).join(' + ');
  out.push(H.banner(`CORE TOTAL: ${sum} = ${W.total} marks`, { size: 26 }));
  return out;
}

// ---------- Lesson plan ----------
function lessonPlan(L) {
  return [...header(L.meta, `Lesson ${L.meta.lesson} Lesson Plan: ${L.meta.topic}`), ...sectionsToDocx(L.lesson_plan)];
}

// ---------- Assessment plan ----------
function answerKey(L) {
  const W = L.worksheet;
  const out = [heading(`Worksheet answer key (${W.total} marks)`),
    para('Same answers and marks as the mark scheme, with the marking rationale for each item.', { italics: true, p: { keepNext: true } })];
  for (const sec of W.sections) {
    out.push(para(`Section ${sec.letter}: ${sec.name} (${sec.marks} marks)`, { bold: true, color: H.NAVY, p: { spacing: { before: 160, after: 80 }, keepNext: true } }));
    out.push(H.itemTable(['Item', 'Question', 'Answer', 'Marking rationale', 'Marks'],
      sec.questions.map((q) => [q.item, q.text, q.answer, q.marking, q.marks]), { widths: [7, 26, 33, 26, 8] }));
  }
  out.push(gap(200));
  return out;
}

function assessmentPlan(L) {
  return [...header(L.meta, `Lesson ${L.meta.lesson} Assessment Plan: ${L.meta.topic}`),
    ...sectionsToDocx(L.assessment_plan, { worksheet_answer_key: () => answerKey(L) })];
}

// Word-based document types this builder can make. course.json "documents" chooses which
// ones a course needs and their file names; lesson.py converts the .pdf ones afterwards.
const BUILDERS = {
  speaker_notes: speakerNotes, worksheet, mark_scheme: markScheme,
  lesson_plan: lessonPlan, assessment_plan: assessmentPlan,
};

/** "{prefix}_Worksheet.pdf" -> "Lesson2_Worksheet.docx" (Word source for every Word/PDF document). */
const docxName = (tmpl, meta) => tmpl.replace(/\{(\w+)\}/g, (_, k) => meta[k] ?? `{${k}}`).replace(/\.(pdf|docx)$/i, '.docx');

async function main(src, outDir) {
  const L = JSON.parse(fs.readFileSync(src, 'utf8'));
  fs.mkdirSync(outDir, { recursive: true });
  for (const doc of (L.config || {}).documents || []) {
    if (!BUILDERS[doc.type]) continue; // deck and glossary are built elsewhere; lesson.py rejects unknown types
    await save(BUILDERS[doc.type](L), path.join(outDir, docxName(doc.file, L.meta)));
  }
}

main(process.argv[2], process.argv[3]).catch((e) => { console.error(e); process.exit(1); });
