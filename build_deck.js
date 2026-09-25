/**
 * Build the lesson slide deck from lesson.json (output of parse_content.py).
 * Usage: node build_deck.js <lesson.json> <out.pptx>
 *
 * Chapter 3 CLAUDE.md rules applied here:
 *   - all content text is 30 pt (BODY_PT); the title may shrink below 30 pt when long
 *   - word limit (35, title excluded) is enforced by check_deck.py, not by shrinking text
 *   - question and answer slides are separate slides in content.md
 * Chrome shapes are named (Title, Tag, Footer, PageNum) so check_deck.py can exclude them.
 */
const fs = require('fs');
const PptxGenJS = require('pptxgenjs');
const S = require('./lib/style');

const BODY_PT = 30;
const BODY = { fontFace: 'Calibri', fontSize: BODY_PT, color: S.NAVY };
const AREA = { x: 0.6, y: 1.4, w: 12.13, h: 5.55 };

const TAG_COLORS = {
  'DO NOW': S.BROWN, 'CFU': S.AMBER, 'STOP & CHECK': S.CORAL,
  'WORTH KNOWING': S.AMBER, 'STRETCH': S.AMBER, 'EXIT TICKET': S.CORAL, 'CREDITS': S.WHITE,
};
const tagColor = (tag) => TAG_COLORS[tag] || S.ICE_BLUE; // never NAVY on the navy bar
const boxFill = (tag) => (tag === 'CFU' ? S.CFU_BG : tag === 'STOP & CHECK' ? S.HINGEPOINT_BG : S.LIGHT_GREY);

function titlePt(title) {
  if (title.length > 54) return 22;
  if (title.length > 46) return 26;
  return 30;
}

function chrome(slide, s, pageNum, footer) {
  slide.addShape('rect', { x: 0, y: 0, w: S.LAYOUT_W, h: 1.05, fill: { color: S.NAVY }, line: { type: 'none' } });
  slide.addText(s.title, {
    x: 0.5, y: 0.12, w: 10.1, h: 0.8, objectName: 'Title',
    fontFace: 'Cambria', fontSize: titlePt(s.title), bold: true, color: S.WHITE, valign: 'middle', fit: 'none',
  });
  if (s.tag) {
    const fill = tagColor(s.tag);
    slide.addShape('roundRect', { x: 10.73, y: 0.28, w: 2.15, h: 0.5, rectRadius: 0.1, fill: { color: fill }, line: { type: 'none' } });
    slide.addText(s.tag, {
      x: 10.73, y: 0.28, w: 2.15, h: 0.5, objectName: 'Tag',
      fontFace: 'Calibri', fontSize: 13, bold: true, align: 'center', valign: 'middle',
      color: [S.ICE_BLUE, S.AMBER, S.WHITE].includes(fill) ? S.NAVY : S.WHITE,
    });
  }
  slide.addText(footer, { x: 0.4, y: 7.15, w: 8.0, h: 0.3, objectName: 'Footer', fontFace: 'Calibri', fontSize: 10, color: S.NAVY });
  slide.addText(String(pageNum), { x: 12.43, y: 7.15, w: 0.5, h: 0.3, objectName: 'PageNum', fontFace: 'Calibri', fontSize: 10, color: S.NAVY, align: 'right' });
}

function paraRuns(lines, { bullet = false } = {}) {
  return lines.map((t, i) => ({
    text: t,
    options: {
      // numbered question lines ("1. …") carry their own number, so no bullet; "3.75 MB" still gets one
      bullet: bullet && !/^\d+\.\s/.test(t) ? { indent: 22 } : false,
      breakLine: i < lines.length - 1,
      paraSpaceAfter: 10,
    },
  }));
}

function layoutTitle(slide, s, meta) {
  slide.background = { color: S.NAVY };
  for (let r = 0; r < 4; r++) for (let c = 0; c < 6; c++) {
    slide.addShape('ellipse', { x: 11.2 + c * 0.3, y: 0.4 + r * 0.3, w: 0.08, h: 0.08, fill: { color: S.DOT }, line: { type: 'none' } });
  }
  slide.addShape('rect', { x: 0.8, y: 3.55, w: 2.2, h: 0.08, fill: { color: S.AMBER }, line: { type: 'none' } });
  slide.addText(s.title, { x: 0.8, y: 2.0, w: 11.5, h: 1.4, objectName: 'Title', fontFace: 'Cambria', fontSize: 44, bold: true, color: S.WHITE, valign: 'bottom' });
  if (s.subtitle) slide.addText(s.subtitle, { x: 0.8, y: 3.85, w: 11.5, h: 1.3, ...BODY, color: S.ICE_BLUE, valign: 'top' });
}

function layoutText(slide, s) {
  slide.addShape('rect', { ...AREA, fill: { color: boxFill(s.tag) }, line: { type: 'none' } });
  slide.addText(paraRuns(s.text), { x: AREA.x + 0.3, y: AREA.y + 0.25, w: AREA.w - 0.6, h: AREA.h - 0.5, ...BODY, valign: 'top' });
}

function layoutBullets(slide, s) {
  const runs = [...paraRuns(s.text), ...paraRuns(s.bullets, { bullet: true })];
  runs.forEach((r, i) => { r.options.breakLine = i < runs.length - 1; });
  if (s.text.length) runs[0].options.bold = true;
  slide.addText(runs, { ...AREA, ...BODY, valign: 'top' });
}

function layoutCards(slide, s) {
  const n = s.cards.length, gap = 0.35;
  const w = (AREA.w - gap * (n - 1)) / n;
  const h = s.text.length ? 3.9 : 5.3;
  s.cards.forEach((c, i) => {
    const x = AREA.x + i * (w + gap);
    slide.addShape('rect', { x, y: AREA.y, w, h, fill: { color: S.LIGHT_GREY }, line: { type: 'none' } });
    slide.addShape('rect', { x, y: AREA.y, w, h: 0.1, fill: { color: S.AMBER }, line: { type: 'none' } });
    slide.addText([
      { text: c.head, options: { bold: true, breakLine: true, paraSpaceAfter: 14 } },
      { text: c.detail, options: {} },
    ], { x: x + 0.25, y: AREA.y + 0.3, w: w - 0.5, h: h - 0.5, ...BODY, valign: 'top' });
  });
  if (s.text.length) {
    slide.addText(paraRuns(s.text), { x: AREA.x, y: AREA.y + h + 0.3, w: AREA.w, h: AREA.h - h - 0.3, ...BODY, bold: true, valign: 'middle' });
  }
}

function layoutTable(slide, s) {
  const rows = s.table;
  const ncol = rows[0].length;
  const longest = [...Array(ncol).keys()].map((c) => Math.max(...rows.map((r) => (r[c] || '').length), 4));
  const total = longest.reduce((a, b) => a + b, 0);
  const colW = longest.map((l) => (l / total) * AREA.w);
  // never narrower than the longest single word at 30 pt (~0.21 in per character + cell margins),
  // or words like "Development" break mid-word; take the extra width from the widest columns
  const minW = [...Array(ncol).keys()].map((c) =>
    Math.max(...rows.map((r) => Math.max(...(r[c] || '').split(/\s+/).map((w) => w.length)))) * 0.21 + 0.3);
  for (let pass = 0; pass < 3; pass++) {
    const short = colW.map((w, c) => Math.max(0, minW[c] - w));
    const need = short.reduce((a, b) => a + b, 0);
    if (need <= 0.001) break;
    const spare = colW.map((w, c) => Math.max(0, w - minW[c]));
    const spareTotal = spare.reduce((a, b) => a + b, 0);
    colW.forEach((w, c) => { colW[c] = w + short[c] - (spareTotal ? (spare[c] / spareTotal) * need : 0); });
  }
  const data = rows.map((r, ri) => r.map((cell) => ({
    text: cell,
    options: ri === 0
      ? { bold: true, color: S.WHITE, fill: { color: S.DOT } }
      : { color: S.NAVY, fill: { color: ri % 2 ? S.WHITE : S.LIGHT_GREY } },
  })));
  slide.addTable(data, {
    x: AREA.x, y: AREA.y, w: AREA.w, colW, fontFace: 'Calibri', fontSize: BODY_PT,
    border: { type: 'solid', pt: 1, color: S.ICE_BLUE }, valign: 'middle', margin: 0.08, rowH: 0.72,
  });
}

function label(slide, text, x, y, w) {
  slide.addText(text, { x, y, w, h: 0.55, ...BODY, bold: true, margin: 0 });
}

/** Straight line between two points; flipH handles lines running bottom-left to top-right. */
function leader(slide, x1, y1, x2, y2, line = { color: S.NAVY, width: 1.5 }) {
  slide.addShape('line', {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.01), h: Math.max(Math.abs(y2 - y1), 0.01),
    flipH: (x2 < x1) !== (y2 < y1), line,
  });
}

const rad = (d) => (d * Math.PI) / 180;

function diagramHdd(slide) {
  const cx = 10.5, cy = 4.25, R = 1.9;
  slide.addShape('ellipse', { x: cx - R, y: cy - R, w: 2 * R, h: 2 * R, fill: { color: S.ICE_BLUE }, line: { color: S.NAVY, width: 2 } });
  // highlighted sector on the outer track (between radii 1.5 and 1.9), 300°–335° clockwise from 3 o'clock
  slide.addShape('blockArc', {
    x: cx - R, y: cy - R, w: 2 * R, h: 2 * R, angleRange: [300, 335], arcThicknessRatio: 0.4 / R,
    fill: { color: S.AMBER }, line: { color: S.NAVY, width: 1 },
  });
  [1.5, 1.1, 0.7].forEach((r) => slide.addShape('ellipse', { x: cx - r, y: cy - r, w: 2 * r, h: 2 * r, fill: { type: 'none' }, line: { color: S.NAVY, width: 1.25 } }));
  slide.addShape('ellipse', { x: cx - 0.22, y: cy - 0.22, w: 0.44, h: 0.44, fill: { color: S.NAVY }, line: { type: 'none' } });
  // read-write arm from a pivot at bottom-right to a head over the middle track
  const hx = cx + 1.3 * Math.cos(rad(25)), hy = cy + 1.3 * Math.sin(rad(25));
  leader(slide, 12.75, 6.75, hx, hy, { color: S.NAVY_DARK, width: 5 });
  slide.addShape('rect', { x: hx - 0.12, y: hy - 0.12, w: 0.24, h: 0.24, fill: { color: S.CORAL }, line: { type: 'none' } });
  slide.addShape('ellipse', { x: 12.6, y: 6.6, w: 0.3, h: 0.3, fill: { color: S.NAVY_DARK }, line: { type: 'none' } });
  // labels with leader lines
  const sx = cx + 1.7 * Math.cos(rad(317)), sy = cy + 1.7 * Math.sin(rad(317));
  label(slide, 'sector', 11.55, 1.45, 1.3);
  leader(slide, 11.95, 2.0, sx, sy);
  // "track" points at the middle track ring (r = 1.1), passing over the outer tracks
  label(slide, 'track', 7.55, 3.97, 1.0);
  leader(slide, 8.5, 4.25, cx - 1.1, cy);
  label(slide, 'head', 12.1, 5.0, 1.0);
}

function diagramOptical(slide) {
  const cx = 10.3, cy = 4.1, R = 1.95;
  slide.addShape('ellipse', { x: cx - R, y: cy - R, w: 2 * R, h: 2 * R, fill: { color: S.LIGHT_GREY }, line: { color: S.NAVY, width: 2 } });
  // spiral track, centre outwards: r grows linearly with angle
  const pts = [];
  const r0 = 0.45, r1 = 1.8, turns = 5, steps = turns * 36;
  for (let i = 0; i <= steps; i++) {
    const a = rad((i * 360) / 36), r = r0 + ((r1 - r0) * i) / steps;
    pts.push({ x: R + r * Math.cos(a), y: R + r * Math.sin(a) });
  }
  slide.addShape('custGeom', { x: cx - R, y: cy - R, w: 2 * R, h: 2 * R, points: pts, line: { color: S.NAVY, width: 1.5 }, fill: { type: 'none' } });
  slide.addShape('ellipse', { x: cx - 0.3, y: cy - 0.3, w: 0.6, h: 0.6, fill: { color: S.WHITE }, line: { color: S.NAVY, width: 1.5 } });
  // spiral label (top-left) with leader to the outer turn
  const px = cx + r1 * Math.cos(rad(225)), py = cy + r1 * Math.sin(rad(225));
  label(slide, 'spiral track', 7.75, 1.45, 2.6);
  leader(slide, 8.4, 2.0, px, py);
  // laser source bottom-right, beam to the track
  slide.addShape('rect', { x: 11.55, y: 6.2, w: 1.3, h: 0.6, fill: { color: S.NAVY }, line: { type: 'none' } });
  slide.addText('laser', { x: 11.55, y: 6.2, w: 1.3, h: 0.6, ...BODY, color: S.WHITE, bold: true, align: 'center', valign: 'middle', margin: 0 });
  const bx = cx + 1.35 * Math.cos(rad(40)), by = cy + 1.35 * Math.sin(rad(40));
  leader(slide, bx, by, 12.0, 6.2, { color: S.CORAL, width: 3, dashType: 'dash' });
  slide.addShape('ellipse', { x: bx - 0.09, y: by - 0.09, w: 0.18, h: 0.18, fill: { color: S.CORAL }, line: { type: 'none' } });
}

function layoutDiagram(slide, s) {
  slide.addText(paraRuns(s.bullets, { bullet: true }), { x: AREA.x, y: AREA.y, w: 6.9, h: AREA.h, ...BODY, valign: 'top' });
  if (s.diagram === 'hdd') diagramHdd(slide);
  else if (s.diagram === 'optical') diagramOptical(slide);
  else throw new Error(`Unknown diagram: ${s.diagram}`);
}

/** Largest box with the image's aspect ratio that fits inside (w, h), centred in it. */
function fit(s, x, y, w, h) {
  const r = s.image_w / s.image_h;
  const iw = Math.min(w, h * r), ih = iw / r;
  return { x: x + (w - iw) / 2, y: y + (h - ih) / 2, w: iw, h: ih };
}

/**
 * Text (bullets and/or plain lines) plus one image. Wide images (aspect >= 2.2, e.g. the
 * DVD layer diagram) go full-width under the text; everything else sits on the right.
 */
function layoutImage(slide, s) {
  const runs = [...paraRuns(s.text), ...paraRuns(s.bullets, { bullet: true })];
  runs.forEach((r, i) => { r.options.breakLine = i < runs.length - 1; });
  const wide = s.image_w / s.image_h >= 2.2;
  const img = { path: s.image, altText: s.credit };
  if (wide) {
    const textH = 2.75;
    slide.addText(runs, { x: AREA.x, y: AREA.y, w: AREA.w, h: textH, ...BODY, valign: 'top' });
    slide.addImage({ ...img, ...fit(s, AREA.x, AREA.y + textH + 0.15, AREA.w, AREA.h - textH - 0.15) });
  } else {
    // landscape images (e.g. Figure 3.7 with its small labels) get more width than portrait ones
    const textW = !runs.length ? 0 : s.image_w / s.image_h >= 1.3 ? 5.5 : 6.3;
    if (runs.length) slide.addText(runs, { x: AREA.x, y: AREA.y, w: textW, h: AREA.h, ...BODY, valign: 'top' });
    const gap = runs.length ? 0.35 : 0;
    slide.addImage({ ...img, ...fit(s, AREA.x + textW + gap, AREA.y, AREA.w - textW - gap, AREA.h) });
  }
}

/** Closing "Image credits" slide: small text by design, exempt from the 30 pt / 35-word rules. */
function layoutCredits(slide, s) {
  slide.addText(s.bullets.map((t, i) => ({ text: t, options: { breakLine: i < s.bullets.length - 1, paraSpaceAfter: 6 } })), {
    ...AREA, fontFace: 'Calibri', fontSize: 13, color: S.NAVY, valign: 'top', objectName: 'Credits',
  });
}

const LAYOUTS = {
  text: layoutText, bullets: layoutBullets, cards: layoutCards, table: layoutTable,
  diagram: layoutDiagram, image: layoutImage, credits: layoutCredits,
};

async function main(src, out) {
  const lesson = JSON.parse(fs.readFileSync(src, 'utf8'));
  const pres = new PptxGenJS();
  pres.layout = 'LAYOUT_WIDE';
  pres.title = `${lesson.meta.deck_name}`;
  lesson.slides.forEach((s, i) => {
    const slide = pres.addSlide();
    if (s.layout === 'title') {
      layoutTitle(slide, s, lesson.meta);
    } else {
      const fn = LAYOUTS[s.layout];
      if (!fn) throw new Error(`Unknown layout "${s.layout}" on slide ${i + 1}`);
      chrome(slide, s, i + 1, lesson.meta.footer);
      fn(slide, s);
    }
    slide.addNotes(s.notes);
  });
  await pres.writeFile({ fileName: out });
  console.log(`Deck: ${lesson.slides.length} slides -> ${out}`);
}

main(process.argv[2], process.argv[3]).catch((e) => { console.error(e); process.exit(1); });
