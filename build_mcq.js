/**
 * Build a chapter's unit MCQ from mcq.json (output of parse_mcq.py).
 * Usage: node build_mcq.js <mcq.json> <out_dir>
 *
 * Writes the two documents named in course.json "unit_mcq.documents":
 *   mcq_paper  student question paper (Word; lesson.py converts it to PDF). Never carries answers.
 *   mcq_key    teacher answer key: summary, lesson coverage, letter distribution, and every
 *              question with its correct option and why each wrong option is wrong.
 * Both come from the same mcq.json, so the key cannot drift from the paper.
 */
const fs = require('fs');
const path = require('path');
const { Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, ShadingType, TabStopType } = require('docx');
const H = require('./lib/docx_helpers');

const { gap, para, heading, save } = H;
const GRID_COLS = 10;

function header(meta, docTitle) {
  return [
    H.banner(docTitle, { size: 30 }),
    para(`${meta.course} · Chapter ${meta.chapter}: ${meta.title}`, { color: H.NAVY, p: { spacing: { before: 100, after: 200 } } }),
  ];
}

// ---------- Question paper (student-facing, no answers) ----------
/**
 * Question stem (wrapped lines hang under the text, not the number), optional table and image,
 * then the options, all in one keepBlock so a question never splits across pages.
 */
function question(q) {
  const out = [new Paragraph({
    spacing: { before: 0, after: 80 }, indent: { left: 500, hanging: 500 },
    tabStops: [{ type: TabStopType.LEFT, position: 500 }],
    children: [
      new TextRun({ text: `${q.number}\t`, bold: true, size: 22, color: H.NAVY }),
      new TextRun({ text: q.text, size: 22 }),
    ],
  })];
  if (q.table.length) out.push(H.itemTable(q.table[0], q.table.slice(1)), gap(80));
  if (q.image) out.push(H.docImage(q, `Diagram for question ${q.number}`, 40));
  q.options.forEach((o) => out.push(new Paragraph({
    spacing: { after: 60 }, indent: { left: 900, hanging: 400 },
    tabStops: [{ type: TabStopType.LEFT, position: 900 }],
    children: [new TextRun({ text: `${o.letter}\t`, bold: true, size: 22 }), new TextRun({ text: o.text, size: 22 })],
  })));
  return [H.keepBlock(out), gap(200)];
}

/** Answer grid: question numbers over empty boxes, GRID_COLS per band. */
function answerGrid(n) {
  const cell = (text, fill) => new TableCell({
    width: { size: Math.floor(100 / GRID_COLS), type: WidthType.PERCENTAGE },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
    margins: { top: 60, bottom: 60, left: 60, right: 60 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true,
      children: [new TextRun({ text, bold: !!fill, color: fill ? H.WHITE : '000000', size: 22 })] })],
  });
  const rows = [];
  for (let start = 1; start <= n; start += GRID_COLS) {
    const nums = [...Array(GRID_COLS)].map((_, i) => start + i);
    rows.push(new TableRow({ cantSplit: true, children: nums.map((k) => cell(k <= n ? String(k) : '', k <= n ? H.DOT : H.LIGHT_GREY)) }));
    rows.push(new TableRow({ cantSplit: true, height: { value: 560, rule: 'atLeast' }, children: nums.map((k) => cell('', k <= n ? undefined : H.LIGHT_GREY)) }));
  }
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows });
}

function paper(M) {
  const n = M.questions.length;
  const out = header(M.meta, `Chapter ${M.meta.chapter} Unit Test: ${M.meta.title}`);
  out.push(H.nameRow(n, 'Score'), gap(120));
  const std = `Time allowed: ${M.meta.minutes} minutes. Answer all ${n} questions. Each question has exactly one correct answer `
    + `and is worth 1 mark. Write the letter of your answer (${M.questions[0].options.map((o) => o.letter).join(', ')}) `
    + 'in the answer grid at the end of the paper. If you change an answer, cross it out clearly.';
  out.push(H.noteBox([std, ...M.instructions].join(' ')), gap(80));
  M.questions.forEach((q) => out.push(...question(q)));
  out.push(H.keepBlock([heading(`Answer grid   ·   Score ____ / ${n}`), answerGrid(n)]));
  if (M.credits.length) {
    out.push(para(`Image credits. ${M.credits.join(' ')}`, { size: 15, italics: true, color: '555555', p: { spacing: { before: 160, after: 0 } } }));
  }
  return out;
}

// ---------- Answer key (teacher) ----------
function key(M) {
  const qs = M.questions;
  const n = qs.length;
  const lessons = Number(M.meta.lessons);
  const out = header(M.meta, `Chapter ${M.meta.chapter} Unit Test Answer Key: ${M.meta.title}`);
  out.push(H.noteBox(`Teacher document: do not distribute. ${n} questions, 1 mark each, total ${n} marks. `
    + `Time allowed: ${M.meta.minutes} minutes. Source: ${M.meta.source || 'see each question'}.`), gap(160));

  out.push(heading('Answer summary'));
  out.push(H.itemTable(['Q', 'Answer', 'Lesson', 'AO'], qs.map((q) => [q.number, q.answer, `L${q.lesson}`, q.ao]), { widths: [15, 25, 30, 30] }), gap(160));

  out.push(heading('Lesson coverage'));
  out.push(H.itemTable(['Lesson', 'Questions', 'Count'], [...Array(lessons)].map((_, i) => {
    const on = qs.filter((q) => q.lesson === i + 1).map((q) => q.number);
    return [`L${i + 1}`, on.join(', ') || 'none', on.length];
  }), { widths: [20, 60, 20] }), gap(160));

  out.push(heading('Answer distribution'));
  const letters = qs[0].options.map((o) => o.letter);
  out.push(H.itemTable(['Letter', 'Correct answer for', 'Share'], letters.map((l) => {
    const c = qs.filter((q) => q.answer === l).length;
    return [l, `${c} question${c === 1 ? '' : 's'}`, `${Math.round((100 * c) / n)}%`];
  }), { widths: [20, 60, 20] }), gap(160));

  out.push(heading('Question-by-question rationale'));
  qs.forEach((q) => {
    const block = [
      para(`Question ${q.number}  ·  L${q.lesson}  ·  ${q.ao}  ·  Answer ${q.answer}`, { bold: true, color: H.NAVY, p: { spacing: { before: 0, after: 60 } } }),
      para(q.text),
      H.itemTable(['Option', 'Text', 'Why it is right or wrong'],
        q.options.map((o) => [o.letter, o.text, o.letter === q.answer ? 'Correct.' : (q.why[o.letter] || '')]), { widths: [13, 37, 50] }),
    ];
    if (q.source) block.push(para(`Source: ${q.source}`, { size: 18, italics: true, color: '555555', p: { spacing: { before: 60 } } }));
    out.push(H.keepBlock(block), gap(160));
  });
  return out;
}

const BUILDERS = { mcq_paper: paper, mcq_key: key };

/** "{prefix}.pdf" -> "Ch3_Unit_MCQ.docx" (Word source for both documents). */
const docxName = (tmpl, meta) => tmpl.replace(/\{(\w+)\}/g, (_, k) => meta[k] ?? `{${k}}`).replace(/\.(pdf|docx)$/i, '.docx');

async function main(src, outDir) {
  const M = JSON.parse(fs.readFileSync(src, 'utf8'));
  fs.mkdirSync(outDir, { recursive: true });
  for (const doc of M.config.unit_mcq.documents) {
    if (!BUILDERS[doc.type]) throw new Error(`unknown unit_mcq document type: ${doc.type}`);
    await save(BUILDERS[doc.type](M), path.join(outDir, docxName(doc.file, M.meta)));
  }
}

main(process.argv[2], process.argv[3]).catch((e) => { console.error(e); process.exit(1); });
