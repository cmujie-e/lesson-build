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
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, AlignmentType, TabStopType, LevelFormat,
} = require('docx');
const H = require('./lib/docx_helpers');

const PAGE = { size: { width: 11906, height: 16838 }, margin: { top: 1000, bottom: 1000, left: 1100, right: 1100 } };
const FONT = 'Calibri';
const NUMBERING = {
  config: [{
    reference: 'bullets',
    levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }],
  }],
};

const gap = (after = 160) => new Paragraph({ spacing: { after }, children: [] });
const para = (text, opts = {}) => new Paragraph({
  spacing: { after: 100 }, ...opts.p,
  children: [new TextRun({ text, size: opts.size || 21, bold: opts.bold, italics: opts.italics, color: opts.color || '000000' })],
});
const bullet = (text) => new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text, size: 21 })] });

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

/**
 * Navy section heading as a shaded paragraph rather than H.banner's one-cell table:
 * a paragraph can carry keepNext, so the heading never sits alone at the foot of a page.
 */
const heading = (text) => new Paragraph({
  keepNext: true,
  spacing: { before: 120, after: 140 },
  shading: { type: ShadingType.CLEAR, fill: H.NAVY },
  indent: { left: 60, right: 60 },
  children: [new TextRun({ text: ` ${text}`, bold: true, color: H.WHITE, size: 24 })],
});

function sectionsToDocx(sections, placeholders = {}) {
  const out = [];
  for (const s of sections) {
    const ph = s.blocks.find((b) => b.type === 'placeholder');
    if (ph) { out.push(...placeholders[ph.name]()); continue; }
    if (s.heading) out.push(heading(s.heading));
    out.push(...blocksToDocx(s.blocks));
    out.push(gap(200));
  }
  return out;
}

async function save(children, file) {
  const doc = new Document({
    styles: { default: { document: { run: { font: FONT } } } },
    numbering: NUMBERING,
    sections: [{ properties: { page: PAGE }, children }],
  });
  fs.writeFileSync(file, await Packer.toBuffer(doc));
  console.log(`  ${path.basename(file)}`);
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

function nameRow(total) {
  const cell = (children, w, fill) => new TableCell({
    width: { size: w, type: WidthType.PERCENTAGE }, children, margins: { top: 120, bottom: 120, left: 140, right: 140 },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [new TableRow({ children: [
      cell([para('Name: ______________________________'), para('Class: ____________   Date: ____________')], 72),
      cell([new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `Total: ____ / ${total}`, bold: true, size: 28, color: H.NAVY })] })], 28, H.CFU_BG),
    ] })],
  });
}

function worksheet(L) {
  const W = L.worksheet;
  const out = header(L.meta, `Lesson ${L.meta.lesson} Worksheet: ${L.meta.topic}`);
  out.push(nameRow(W.total), gap(120), para(W.intro, { italics: true }), gap(120));
  for (const sec of W.sections) {
    out.push(H.banner(`Section ${sec.letter}: ${sec.name}   ·   ${sec.marks} mark${sec.marks === 1 ? '' : 's'}`, { size: 24 }));
    out.push(gap(80));
    if (sec.wordbank) out.push(H.noteBox(`Word bank:  ${sec.wordbank}`, { size: 22 }), gap(80));
    sec.instructions.forEach((t) => out.push(para(t, { italics: true })));
    if (sec.reference.length) {
      out.push(para(sec.reference_title, { bold: true, color: H.NAVY }));
      out.push(H.itemTable(sec.reference[0], sec.reference.slice(1)), gap(120));
    }
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
      out.push(...answerLines(q.lines));
    }
    out.push(gap(240));
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
    out.push(H.banner(`Section ${sec.letter}: ${sec.name} (${sec.marks} marks)   ·   running total ${running} / ${W.total}`, { size: 22 }));
    out.push(gap(60));
    out.push(H.itemTable(['Item', 'Accepted answer', 'Marks'], sec.questions.map((q) => [q.item, q.answer, q.marks]), { widths: [9, 80, 11] }));
    out.push(gap(200));
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
    para('Same answers and marks as the mark scheme, with the marking rationale for each item.', { italics: true })];
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

async function main(src, outDir) {
  const L = JSON.parse(fs.readFileSync(src, 'utf8'));
  const p = L.meta.prefix;
  fs.mkdirSync(outDir, { recursive: true });
  await save(speakerNotes(L), path.join(outDir, `${p}_Speaker_Notes.docx`));
  await save(worksheet(L), path.join(outDir, `${p}_Worksheet.docx`));
  await save(markScheme(L), path.join(outDir, `${p}_Mark_Scheme.docx`));
  await save(lessonPlan(L), path.join(outDir, `${p}_Lesson_Plan.docx`));
  await save(assessmentPlan(L), path.join(outDir, `${p}_Assessment_Plan.docx`));
}

main(process.argv[2], process.argv[3]).catch((e) => { console.error(e); process.exit(1); });
