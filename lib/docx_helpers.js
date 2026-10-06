/**
 * Shared docx helper functions — extracted and verified against the actual
 * built Lesson 2 files (Mark Scheme, Assessment Plan, Lesson Plan, Submission
 * Sheet .docx), not reconstructed from the prose spec alone. Uses the `docx`
 * npm package. Colours read directly from the shipped Mark Scheme's table
 * shading XML.
 *
 * Confirmed table-shading pattern (Lesson2_Mark_Scheme.docx):
 *   - Section banner: 1x1 table, single cell, fill 1E2761 (NAVY), white bold text
 *   - Marking-philosophy / note box: 1x1 table, fill FFF6E0 (same CFU amber-tint
 *     used in the slide deck)
 *   - Item table header row: fill 3A4488 (a lighter navy — same colour used
 *     for the decorative corner-dots on the deck's title slide), white bold text
 *   - Item table body rows: alternating WHITE / F4F6FC shading
 */

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Table, TableRow, TableCell, Paragraph, TextRun, ImageRun,
  WidthType, ShadingType, VerticalAlign, AlignmentType, BorderStyle, LevelFormat,
} = require('docx');

const NAVY = '1E2761';
const DOT = '3A4488';
const CFU_BG = 'FFF6E0';
const HINGEPOINT_BG = 'FFEAD1';
const LIGHT_GREY = 'F4F6FC';
const WHITE = 'FFFFFF';

function noBorders() {
  const none = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
  return { top: none, bottom: none, left: none, right: none };
}

/**
 * Full-width single-cell banner — used for section headers on the worksheet,
 * mark scheme, and submission sheet. Matches the NAVY section banner pattern.
 */
function banner(text, { fill = NAVY, textColor = WHITE, bold = true, size = 24 } = {}) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill },
            verticalAlign: VerticalAlign.CENTER,
            margins: { top: 120, bottom: 120, left: 160, right: 160 },
            borders: noBorders(),
            children: [
              new Paragraph({
                children: [new TextRun({ text, bold, color: textColor, size })],
              }),
            ],
          }),
        ],
      }),
    ],
  });
}

/**
 * Full-width note box — marking-philosophy note, CFU box, hingepoint decision
 * rule box, etc. Same visual pattern as `banner()` but a lighter tint fill
 * and non-bold body text, matching the deck's CFU_BG / HINGEPOINT_BG tones.
 */
function noteBox(text, { fill = CFU_BG, textColor = NAVY, size = 20 } = {}) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill },
            margins: { top: 160, bottom: 160, left: 200, right: 200 },
            borders: noBorders(),
            children: [
              new Paragraph({
                children: [new TextRun({ text, color: textColor, size })],
              }),
            ],
          }),
        ],
      }),
    ],
  });
}

/**
 * Item / mark-scheme style table: header row shaded DOT (3A4488), body rows
 * alternating WHITE / LIGHT_GREY. `rows` is an array of arrays of strings,
 * `header` is an array of header cell strings (e.g. ['Item', 'Accepted answer', 'Marks']).
 */
/**
 * Column widths (percent) weighted by each column's longest text, with a floor so short
 * columns (Item, Marks) stay narrow but readable. Equal widths squeeze long answer text.
 */
function autoWidths(header, rows) {
  const n = header.length;
  const len = [...Array(n)].map((_, c) => Math.max(...[header, ...rows].map((r) => String(r[c] ?? '').length)));
  const w = len.map((l) => Math.min(Math.max(Math.sqrt(l), 2.6), 12));
  const total = w.reduce((a, b) => a + b, 0);
  return w.map((x) => (x / total) * 100);
}

function itemTable(header, rows, { headerFill = DOT, altFill = LIGHT_GREY, widths, keepTogether = false } = {}) {
  // keepTogether: keepNext on every row's paragraph, so the table never splits across pages
  // and stays with whatever follows it (used for worksheet reference tables)
  const pct = widths || autoWidths(header, rows);
  const cellWidth = (c) => ({ size: Math.round(pct[c]), type: WidthType.PERCENTAGE }); // docx v9 takes whole percent
  const headerRow = new TableRow({
    tableHeader: true,
    cantSplit: true,
    children: header.map((h, ci) =>
      new TableCell({
        width: cellWidth(ci),
        shading: { type: ShadingType.CLEAR, fill: headerFill },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: [new Paragraph({ keepNext: keepTogether, children: [new TextRun({ text: h, bold: true, color: WHITE, size: 20 })] })],
      })
    ),
  });

  const bodyRows = rows.map((cells, i) =>
    new TableRow({
      cantSplit: true,
      children: cells.map((c, ci) =>
        new TableCell({
          width: cellWidth(ci),
          shading: { type: ShadingType.CLEAR, fill: i % 2 === 0 ? WHITE : altFill },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ keepNext: keepTogether, children: [new TextRun({ text: String(c), size: 20 })] })],
        })
      ),
    })
  );

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: pct.map((p) => Math.round(p * 97)), // twips across ~9700 usable width
    rows: [headerRow, ...bodyRows],
  });
}

// ---------- Page, paragraphs and saving (shared by build_docs.js and build_mcq.js) ----------
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

/**
 * Navy section heading as a shaded paragraph rather than banner()'s one-cell table:
 * a paragraph can carry keepNext, so the heading never sits alone at the foot of a page.
 */
const heading = (text) => new Paragraph({
  keepNext: true,
  spacing: { before: 120, after: 140 },
  shading: { type: ShadingType.CLEAR, fill: NAVY },
  indent: { left: 60, right: 60 },
  children: [new TextRun({ text: ` ${text}`, bold: true, color: WHITE, size: 24 })],
});

/** Student details box with a marks total on the right ("Total: ____ / 12", "Score: ____ / 16"). */
function nameRow(total, label = 'Total') {
  const cell = (children, w, fill) => new TableCell({
    width: { size: w, type: WidthType.PERCENTAGE }, children, margins: { top: 120, bottom: 120, left: 140, right: 140 },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [new TableRow({ children: [
      cell([para('Name: ______________________________'), para('Class: ____________   Date: ____________')], 72),
      cell([new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: `${label}: ____ / ${total}`, bold: true, size: 28, color: NAVY })] })], 28, CFU_BG),
    ] })],
  });
}

/**
 * A document diagram (worksheet section or question, MCQ question), max ~9.5 cm wide or 7 cm tall
 * (docx sizes are in 96-dpi pixels); wide strips (aspect >= 2.5, e.g. a row of symbols) may use
 * the full text width; an explicit width: overrides both. keepNext holds it to the lines that follow.
 * obj: { image, image_w, image_h, credit, width } as recorded by the parser.
 */
function docImage(obj, title, before = 0) {
  // "width: <cm>" in the source sets the printed width (capped at the text width, 17 cm)
  const maxW = obj.width ? Math.min(obj.width * 37.8, 640) : obj.image_w / obj.image_h >= 2.5 ? 640 : 360;
  const scale = Math.min(maxW / obj.image_w, (obj.width ? 400 : 265) / obj.image_h);
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before, after: 160 }, keepNext: true,
    children: [new ImageRun({
      type: path.extname(obj.image).toLowerCase() === '.png' ? 'png' : 'jpg',
      data: fs.readFileSync(obj.image),
      transformation: { width: Math.round(obj.image_w * scale), height: Math.round(obj.image_h * scale) },
      altText: { title, description: obj.credit, name: path.basename(obj.image) },
    })],
  });
}

/**
 * Keep a group of paragraphs/tables on one page: a borderless one-cell table whose single row
 * cannot split. keepNext alone does not hold a table to the paragraphs after it in LibreOffice
 * (an MCQ question's truth table was split from its diagram and options that way).
 * A cell must end with a paragraph, so an empty one is added after a trailing table.
 */
function keepBlock(children) {
  const body = children[children.length - 1] instanceof Table ? [...children, new Paragraph({ children: [] })] : children;
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { ...noBorders(), insideHorizontal: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, insideVertical: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' } },
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      borders: noBorders(), margins: { top: 0, bottom: 0, left: 0, right: 0 }, children: body,
    })] })],
  });
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

module.exports = {
  banner, noteBox, itemTable, noBorders,
  gap, para, bullet, heading, nameRow, docImage, keepBlock, save, PAGE, FONT, NUMBERING,
  NAVY, DOT, CFU_BG, HINGEPOINT_BG, LIGHT_GREY, WHITE,
};
