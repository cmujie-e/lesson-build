/**
 * Shared pptxgenjs slide-chrome helpers — extracted and verified against the
 * actual built Lesson 2 deck (Lesson2_Hexadecimal_BCD_CharacterSets.pptx),
 * not reconstructed from the prose spec alone. Coordinates, fills and fonts
 * below are read directly from that file's shape XML.
 *
 * Corrected palette (SKILL.md's documented palette was incomplete — these
 * colours are actually used in the shipped deck and were missing from the
 * written spec):
 *   CORAL       E76F51   — hingepoint "STOP & CHECK" tag pill + warning icon
 *   CORAL_BG    FFF0EC   — hingepoint warning icon circle background
 *   BROWN       8B5E3C   — "DO NOW" retrieval-practice icon on slide 2
 *   LIGHT_GREY  F4F6FC   — neutral content box background (Career Link cards,
 *                          CFU content boxes, checkbox background)
 *   DOT         3A4488   — decorative corner-dot/grid marks on the title slide,
 *                          also used as the item-table header shade in docx
 *
 * Confirmed from the built file (not previously documented):
 *   - Title bar text: Cambria, 30pt, bold, white
 *   - Binary/hex/monospace text: Courier New, 12–14pt
 *   - Title bar: NAVY (1E2761), full width, 1.05" tall
 *   - Tag pill: top-right, x≈10.73, y≈0.28, w=2.15, h=0.5
 *   - Footer: left = "<Course label> • Ch<N> L<N> • <Topic>" at (0.4, 7.15, 8.0x0.3);
 *             right = page number at (12.43, 7.15, 0.5x0.3)
 */

const NAVY = '1E2761';
const NAVY_DARK = '141B47';
const ICE_BLUE = 'CADCFC';
const WHITE = 'FFFFFF';
const AMBER = 'FFC857';
const CFU_BG = 'FFF6E0';
const HINGEPOINT_BG = 'FFEAD1';
const CORAL = 'E76F51';
const CORAL_BG = 'FFF0EC';
const BROWN = '8B5E3C';
const LIGHT_GREY = 'F4F6FC';
const DOT = '3A4488';

const LAYOUT_W = 13.33;
const LAYOUT_H = 7.5;

/** Full-width navy title bar with white Cambria title text and a coloured tag pill top-right. */
function titleBar(slide, { title, tag, tagColor = NAVY } = {}) {
  slide.addShape('rect', {
    x: 0, y: 0, w: LAYOUT_W, h: 1.05,
    fill: { color: NAVY }, line: { type: 'none' },
  });
  slide.addText(title, {
    x: 0.5, y: 0.12, w: 10.5, h: 0.8,
    fontFace: 'Cambria', fontSize: 30, bold: true, color: WHITE,
    valign: 'middle',
  });
  if (tag) {
    slide.addShape('roundRect', {
      x: 10.73, y: 0.28, w: 2.15, h: 0.5, rectRadius: 0.1,
      fill: { color: tagColor }, line: { type: 'none' },
    });
    // white text on NAVY/CORAL tags, navy text on light tags (ICE_BLUE/AMBER) — pick for contrast
    const lightTags = [ICE_BLUE, AMBER];
    const tagTextColor = lightTags.includes(tagColor) ? NAVY : WHITE;
    slide.addText(tag, {
      x: 10.73, y: 0.28, w: 2.15, h: 0.5,
      fontFace: 'Calibri', fontSize: 13, bold: true, color: tagTextColor,
      align: 'center', valign: 'middle',
    });
  }
}

/** Footer chrome: course/chapter/lesson label bottom-left, page number bottom-right. */
function footerChrome(slide, { label, pageNum } = {}) {
  slide.addText(label, {
    x: 0.4, y: 7.15, w: 8.0, h: 0.3,
    fontFace: 'Calibri', fontSize: 10, color: NAVY,
  });
  slide.addText(String(pageNum), {
    x: 12.43, y: 7.15, w: 0.5, h: 0.3,
    fontFace: 'Calibri', fontSize: 10, color: NAVY, align: 'right',
  });
}

/** Small numbered navy circle badge (used for LO list items and STEP slide numerals). */
function numberedCircle(slide, { x, y, size = 0.45, number, fill = NAVY, textColor = WHITE } = {}) {
  slide.addShape('ellipse', {
    x, y, w: size, h: size,
    fill: { color: fill }, line: { type: 'none' },
  });
  slide.addText(String(number), {
    x, y, w: size, h: size,
    fontFace: 'Calibri', fontSize: 16, bold: true, color: textColor,
    align: 'center', valign: 'middle',
  });
}

/** Generic rounded content box with a fill colour — CFU (FFF6E0), hingepoint (FFEAD1), neutral (F4F6FC), etc. */
function contentBox(slide, { x, y, w, h, fill = LIGHT_GREY } = {}) {
  slide.addShape('rect', {
    x, y, w, h,
    fill: { color: fill }, line: { type: 'none' },
  });
}

/** Monospace text for binary/hex/BCD sequences and worked-example figures. */
function monoText(slide, text, { x, y, w, h, size = 14, color = NAVY, bold = false } = {}) {
  slide.addText(text, {
    x, y, w, h,
    fontFace: 'Courier New', fontSize: size, color, bold,
  });
}

module.exports = {
  titleBar, footerChrome, numberedCircle, contentBox, monoText,
  NAVY, NAVY_DARK, ICE_BLUE, WHITE, AMBER, CFU_BG, HINGEPOINT_BG,
  CORAL, CORAL_BG, BROWN, LIGHT_GREY, DOT, LAYOUT_W, LAYOUT_H,
};
