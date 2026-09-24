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

const {
  Table, TableRow, TableCell, Paragraph, TextRun,
  WidthType, ShadingType, VerticalAlign, AlignmentType, BorderStyle,
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

function itemTable(header, rows, { headerFill = DOT, altFill = LIGHT_GREY, widths } = {}) {
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
        children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: WHITE, size: 20 })] })],
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
          children: [new Paragraph({ children: [new TextRun({ text: String(c), size: 20 })] })],
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

module.exports = {
  banner, noteBox, itemTable, noBorders,
  NAVY, DOT, CFU_BG, HINGEPOINT_BG, LIGHT_GREY, WHITE,
};
