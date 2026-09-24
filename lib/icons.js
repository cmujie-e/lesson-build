/**
 * Shared ICT icon library — pptxgenjs
 *
 * House-style constraint (see SKILL.md §5): icons are built ONLY from
 * pptxgenjs primitives (rect, roundRect, ellipse, triangle, line, blockArc).
 * No external/downloaded images — zero copyright risk, consistent style
 * across every lesson and every course.
 *
 * Palette (see SKILL.md §5):
 *   NAVY       1E2761
 *   NAVY_DARK  141B47
 *   ICE_BLUE   CADCFC
 *   WHITE      FFFFFF
 *   AMBER      FFC857
 *
 * Usage:
 *   const icons = require('./icons.js');
 *   icons.storageDrive(slide, { x: 1, y: 1, size: 1.2 });
 *
 * Every function takes (slide, opts):
 *   opts.x, opts.y   — top-left position in inches
 *   opts.size        — bounding box size in inches (icons are drawn to fit
 *                      a size x size square unless noted otherwise)
 *   opts.color       — primary line/fill colour, defaults to NAVY
 *   opts.accent      — secondary accent colour, defaults to AMBER
 *
 * Stroke width follows the established house rule: Math.max(minPoints, s * factor)
 * so outline-only icons never render as near-invisible hairlines at small sizes.
 */

const NAVY = '1E2761';
const NAVY_DARK = '141B47';
const ICE_BLUE = 'CADCFC';
const WHITE = 'FFFFFF';
const AMBER = 'FFC857';

function strokeWidth(size, factor = 2.2, minPoints = 1.5) {
  return Math.max(minPoints, size * factor);
}

/** External storage drive: rounded-rect body, activity light, two grille lines. */
function storageDrive(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const sw = strokeWidth(size);
  slide.addShape('roundRect', {
    x, y, w: size, h: size * 0.62,
    rectRadius: size * 0.08,
    fill: { color: WHITE },
    line: { color, width: sw },
  });
  // grille lines
  slide.addShape('line', {
    x: x + size * 0.12, y: y + size * 0.2, w: size * 0.5, h: 0,
    line: { color, width: sw * 0.6 },
  });
  slide.addShape('line', {
    x: x + size * 0.12, y: y + size * 0.34, w: size * 0.5, h: 0,
    line: { color, width: sw * 0.6 },
  });
  // activity light
  slide.addShape('ellipse', {
    x: x + size * 0.72, y: y + size * 0.24, w: size * 0.12, h: size * 0.12,
    fill: { color: accent }, line: { type: 'none' },
  });
}

/** Keyboard: rounded-rect base + grid of small key rects. */
function keyboard(slide, { x, y, size = 1, color = NAVY } = {}) {
  const sw = strokeWidth(size);
  const w = size, h = size * 0.55;
  slide.addShape('roundRect', {
    x, y, w, h, rectRadius: size * 0.06,
    fill: { color: WHITE }, line: { color, width: sw },
  });
  const cols = 6, rows = 2;
  const padX = w * 0.08, padY = h * 0.15;
  const cellW = (w - padX * 2) / cols;
  const cellH = (h - padY * 2) / rows;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      slide.addShape('rect', {
        x: x + padX + c * cellW + cellW * 0.08,
        y: y + padY + r * cellH + cellH * 0.08,
        w: cellW * 0.84, h: cellH * 0.7,
        fill: { color: ICE_BLUE }, line: { color, width: sw * 0.4 },
      });
    }
  }
}

/** Globe: outer circle + one vertical meridian ellipse + one horizontal line (equator). */
function globe(slide, { x, y, size = 1, color = NAVY } = {}) {
  const sw = strokeWidth(size);
  slide.addShape('ellipse', {
    x, y, w: size, h: size,
    fill: { type: 'none' }, line: { color, width: sw },
  });
  // meridian (narrow ellipse inside, same height)
  slide.addShape('ellipse', {
    x: x + size * 0.32, y, w: size * 0.36, h: size,
    fill: { type: 'none' }, line: { color, width: sw * 0.7 },
  });
  // equator
  slide.addShape('line', {
    x, y: y + size / 2, w: size, h: 0,
    line: { color, width: sw * 0.7 },
  });
}

/** Hex-colour swatch: rounded rect chip in the given hex colour, navy border. Not a hexagon shape — house style restricts icons to the six named primitives, and a "hex swatch" means a swatch of a hex colour, not hexagon geometry. */
function hexSwatch(slide, { x, y, size = 1, hex = AMBER, color = NAVY } = {}) {
  const sw = strokeWidth(size, 1.6, 1);
  slide.addShape('roundRect', {
    x, y, w: size, h: size * 0.6,
    rectRadius: size * 0.1,
    fill: { color: hex.replace('#', '') },
    line: { color, width: sw },
  });
}

/** Seven-segment display digit "8" (all segments on by default) — built from thin rects only. */
function sevenSegmentDisplay(slide, { x, y, size = 1, color = NAVY, on = null } = {}) {
  // on: optional array of 7 booleans [a,b,c,d,e,f,g] to light specific segments; default all on.
  const seg = on || [true, true, true, true, true, true, true];
  const h = size, w = size * 0.55;
  const t = size * 0.1; // segment thickness
  const litColor = color;
  const offColor = ICE_BLUE;
  const halfGap = h / 2 - t * 1.5; // vertical run length of each side segment
  const segs = {
    a: { x: x + t, y: y, w: w - 2 * t, h: t },                                   // top
    b: { x: x + w - t, y: y + t, w: t, h: halfGap },                             // top-right
    c: { x: x + w - t, y: y + h / 2 + t * 0.5, w: t, h: halfGap },               // bottom-right
    d: { x: x + t, y: y + h - t, w: w - 2 * t, h: t },                           // bottom
    e: { x, y: y + h / 2 + t * 0.5, w: t, h: halfGap },                          // bottom-left
    f: { x, y: y + t, w: t, h: halfGap },                                        // top-left
    g: { x: x + t, y: y + h / 2 - t / 2, w: w - 2 * t, h: t },                   // middle
  };
  const order = ['a', 'b', 'c', 'd', 'e', 'f', 'g'];
  order.forEach((k, i) => {
    slide.addShape('rect', {
      ...segs[k],
      fill: { color: seg[i] ? litColor : offColor },
      line: { type: 'none' },
    });
  });
}

/** CPU / processor chip: centered square body with symmetric pin lines on all four sides. */
function cpu(slide, { x, y, size = 1, color = NAVY } = {}) {
  const sw = strokeWidth(size);
  const body = size * 0.6;
  const off = (size - body) / 2; // margin between bounding box and chip body
  const pinLen = off * 0.85;     // pins stay within the margin, don't touch the bounding box edge
  const pins = 4;
  for (let i = 0; i < pins; i++) {
    const pos = off + (body / pins) * (i + 0.5); // evenly spaced along the body edge, inset from corners
    // top & bottom pins
    slide.addShape('line', { x: x + pos, y: y + off - pinLen, w: 0, h: pinLen, line: { color, width: sw * 0.6 } });
    slide.addShape('line', { x: x + pos, y: y + off + body, w: 0, h: pinLen, line: { color, width: sw * 0.6 } });
    // left & right pins
    slide.addShape('line', { x: x + off - pinLen, y: y + pos, w: pinLen, h: 0, line: { color, width: sw * 0.6 } });
    slide.addShape('line', { x: x + off + body, y: y + pos, w: pinLen, h: 0, line: { color, width: sw * 0.6 } });
  }
  slide.addShape('rect', {
    x: x + off, y: y + off, w: body, h: body,
    fill: { color: WHITE }, line: { color, width: sw },
  });
}

/** Padlock: rounded-rect body + shackle arc (blockArc). */
function padlock(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const sw = strokeWidth(size);
  const bodyH = size * 0.55;
  slide.addShape('roundRect', {
    x, y: y + size * 0.45, w: size, h: bodyH,
    rectRadius: size * 0.08,
    fill: { color: accent }, line: { color, width: sw },
  });
  slide.addShape('blockArc', {
    x: x + size * 0.15, y, w: size * 0.7, h: size * 0.7,
    angleRange: [180, 360],
    arcThickness: 'md',
    fill: { type: 'none' }, line: { color, width: sw },
  });
  slide.addShape('ellipse', {
    x: x + size * 0.44, y: y + size * 0.62, w: size * 0.12, h: size * 0.12,
    fill: { color: NAVY_DARK }, line: { type: 'none' },
  });
}

/** Cloud (storage/network): three overlapping ellipses + base rect, outline only. */
function cloud(slide, { x, y, size = 1, color = NAVY } = {}) {
  const sw = strokeWidth(size, 1.8, 1.2);
  slide.addShape('ellipse', { x: x + size * 0.05, y: y + size * 0.25, w: size * 0.45, h: size * 0.4, fill: { color: WHITE }, line: { color, width: sw } });
  slide.addShape('ellipse', { x: x + size * 0.35, y: y + size * 0.05, w: size * 0.5, h: size * 0.5, fill: { color: WHITE }, line: { color, width: sw } });
  slide.addShape('ellipse', { x: x + size * 0.55, y: y + size * 0.3, w: size * 0.4, h: size * 0.35, fill: { color: WHITE }, line: { color, width: sw } });
  slide.addShape('roundRect', { x: x + size * 0.08, y: y + size * 0.45, w: size * 0.84, h: size * 0.22, rectRadius: size * 0.08, fill: { color: WHITE }, line: { color, width: sw } });
}

/**
 * Network hardware device icons — added for Chapter 2 Lesson 2 (network hardware
 * + topologies). All built from a common labelled-box pattern (roundRect body +
 * short device-type label inside) plus a small distinguishing glyph, since these
 * devices have no single universally-drawn symbol at this syllabus level and
 * inventing one risks a technically misleading diagram — the label is the
 * unambiguous part, the glyph is a supporting visual cue only.
 */
function deviceBox(slide, { x, y, w, h, label, color = NAVY, fill = WHITE, labelSize } = {}) {
  const sw = strokeWidth(Math.min(w, h), 2.4, 1.2);
  slide.addShape('roundRect', {
    x, y, w, h, rectRadius: Math.min(w, h) * 0.08,
    fill: { color: fill }, line: { color, width: sw },
  });
  if (label) {
    slide.addText(label, {
      x, y, w, h, fontFace: 'Calibri', fontSize: labelSize || Math.max(8, h * 22),
      bold: true, color, align: 'center', valign: 'middle',
    });
  }
}

/** Hub: labelled box + several equal-size dots radiating out — every port gets the same signal. */
function hubIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const w = size, h = size * 0.5;
  deviceBox(slide, { x, y, w, h, label: 'HUB', color });
  const n = 4;
  for (let i = 0; i < n; i++) {
    const px = x + w + size * 0.12;
    const py = y + (h / (n + 1)) * (i + 1) - size * 0.03;
    slide.addShape('line', { x: x + w, y: y + h / 2, w: px - (x + w), h: py - (y + h / 2), line: { color: accent, width: strokeWidth(size, 1.2, 1) } });
    slide.addShape('ellipse', { x: px, y: py, w: size * 0.06, h: size * 0.06, fill: { color: accent }, line: { type: 'none' } });
  }
}

/** Switch: labelled box + one highlighted port (dashed to the rest) — sends only to the addressed port. */
function switchIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const w = size, h = size * 0.5;
  deviceBox(slide, { x, y, w, h, label: 'SWITCH', color });
  const n = 4;
  for (let i = 0; i < n; i++) {
    const px = x + w + size * 0.12;
    const py = y + (h / (n + 1)) * (i + 1) - size * 0.03;
    const isTarget = i === 1;
    slide.addShape('line', {
      x: x + w, y: y + h / 2, w: px - (x + w), h: py - (y + h / 2),
      line: { color: isTarget ? accent : ICE_BLUE, width: strokeWidth(size, 1.2, 1), dashType: isTarget ? 'solid' : 'dash' },
    });
    slide.addShape('ellipse', { x: px, y: py, w: size * 0.06, h: size * 0.06, fill: { color: isTarget ? accent : ICE_BLUE }, line: { color, width: 0.5 } });
  }
}

/** Repeater: small wave in, larger wave out — boosts/amplifies a signal. */
function repeaterIcon(slide, { x, y, size = 1, color = NAVY } = {}) {
  const w = size, h = size * 0.5;
  deviceBox(slide, { x, y, w, h, label: 'REPEATER', color, labelSize: Math.max(7, h * 16) });
  const sw = strokeWidth(size, 1.4, 1);
  // small wave (input, left of box)
  slide.addShape('line', { x: x - size * 0.28, y: y + h * 0.5, w: size * 0.1, h: -size * 0.08, line: { color, width: sw } });
  slide.addShape('line', { x: x - size * 0.18, y: y + h * 0.42, w: size * 0.1, h: size * 0.16, line: { color, width: sw } });
  slide.addShape('line', { x: x - size * 0.08, y: y + h * 0.58, w: size * 0.08, h: -size * 0.08, line: { color, width: sw } });
  // large wave (output, right of box)
  const ox = x + w + size * 0.1;
  slide.addShape('line', { x: ox, y: y + h * 0.5, w: size * 0.14, h: -size * 0.22, line: { color, width: sw } });
  slide.addShape('line', { x: ox + size * 0.14, y: y + h * 0.28, w: size * 0.14, h: size * 0.44, line: { color, width: sw } });
  slide.addShape('line', { x: ox + size * 0.28, y: y + h * 0.72, w: size * 0.14, h: -size * 0.22, line: { color, width: sw } });
}

/** Bridge: two device boxes joined by a short spanning link — connects two LANs as one. */
function bridgeIcon(slide, { x, y, size = 1, color = NAVY } = {}) {
  const bw = size * 0.42, bh = size * 0.32;
  deviceBox(slide, { x, y: y + size * 0.09, w: bw, h: bh, label: 'LAN A', color, labelSize: Math.max(7, bh * 20) });
  deviceBox(slide, { x: x + size * 0.58, y: y + size * 0.09, w: bw, h: bh, label: 'LAN B', color, labelSize: Math.max(7, bh * 20) });
  slide.addShape('rect', { x: x + bw - size * 0.04, y: y + size * 0.09, w: size * 0.16, h: bh, fill: { color }, line: { type: 'none' } });
  slide.addText('BRIDGE', {
    x: x - size * 0.1, y: y + size * 0.44, w: size * 1.2, h: size * 0.16,
    fontFace: 'Calibri', fontSize: Math.max(7, size * 8), bold: true, color, align: 'center',
  });
}

/** Router: labelled box + several diverging arrows to different destinations — calculates a route. */
function routerIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const w = size, h = size * 0.5;
  deviceBox(slide, { x, y, w, h, label: 'ROUTER', color });
  const angles = [-0.5, 0, 0.5];
  angles.forEach((a) => {
    const ex = x + w + size * 0.22;
    const ey = y + h / 2 + a * size * 0.22;
    slide.addShape('line', { x: x + w, y: y + h / 2, w: ex - (x + w), h: ey - (y + h / 2), line: { color: accent, width: strokeWidth(size, 1.2, 1) } });
    slide.addShape('triangle', { x: ex - size * 0.02, y: ey - size * 0.03, w: size * 0.06, h: size * 0.06, rotate: 90 - a * 60, fill: { color: accent }, line: { type: 'none' } });
  });
}

/** Gateway: labelled box + a frame/doorway with an arrow passing through — an entrance to another network. */
function gatewayIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const w = size, h = size * 0.5;
  deviceBox(slide, { x, y, w, h, label: 'GATEWAY', color, labelSize: Math.max(7, h * 15) });
  const gx = x + w + size * 0.14, gw = size * 0.05, gh = h * 0.9;
  slide.addShape('rect', { x: gx, y: y + h * 0.05, w: gw, h: gh, fill: { color }, line: { type: 'none' } });
  slide.addShape('rect', { x: gx + size * 0.22, y: y + h * 0.05, w: gw, h: gh, fill: { color }, line: { type: 'none' } });
  slide.addShape('line', { x: x + w, y: y + h / 2, w: size * 0.34, h: 0, line: { color: accent, width: strokeWidth(size, 1.4, 1) } });
  slide.addShape('triangle', { x: x + w + size * 0.32, y: y + h / 2 - size * 0.035, w: size * 0.07, h: size * 0.07, rotate: 90, fill: { color: accent }, line: { type: 'none' } });
}

/** Modem: analogue wave in, digital square wave out — modulates/demodulates between the two. */
function modemIcon(slide, { x, y, size = 1, color = NAVY } = {}) {
  const w = size, h = size * 0.5;
  deviceBox(slide, { x, y, w, h, label: 'MODEM', color });
  const sw = strokeWidth(size, 1.4, 1);
  // analogue wave (left)
  const wx = x - size * 0.32, wy = y + h / 2;
  slide.addShape('line', { x: wx, y: wy, w: size * 0.08, h: -size * 0.1, line: { color, width: sw } });
  slide.addShape('line', { x: wx + size * 0.08, y: wy - size * 0.1, w: size * 0.08, h: size * 0.2, line: { color, width: sw } });
  slide.addShape('line', { x: wx + size * 0.16, y: wy + size * 0.1, w: size * 0.08, h: -size * 0.1, line: { color, width: sw } });
  // digital square wave (right)
  const dx = x + w + size * 0.1, dy = y + h * 0.3, dl = size * 0.06;
  slide.addShape('line', { x: dx, y: dy + size * 0.2, w: dl, h: 0, line: { color, width: sw } });
  slide.addShape('line', { x: dx + dl, y: dy, w: 0, h: size * 0.2, line: { color, width: sw } });
  slide.addShape('line', { x: dx + dl, y: dy, w: dl, h: 0, line: { color, width: sw } });
  slide.addShape('line', { x: dx + dl * 2, y: dy, w: 0, h: size * 0.2, line: { color, width: sw } });
  slide.addShape('line', { x: dx + dl * 2, y: dy + size * 0.2, w: dl, h: 0, line: { color, width: sw } });
}

/** NIC: small card/chip with an edge-connector notch and a single port. */
function nicIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER, label = 'NIC' } = {}) {
  const w = size * 0.75, h = size * 0.5;
  slide.addShape('roundRect', { x, y, w, h, rectRadius: size * 0.04, fill: { color: WHITE }, line: { color, width: strokeWidth(size, 1.8, 1) } });
  slide.addShape('rect', { x: x + w * 0.1, y: y + h * 0.2, w: w * 0.35, h: h * 0.15, fill: { color: ICE_BLUE }, line: { type: 'none' } });
  slide.addShape('rect', { x: x + w * 0.1, y: y + h * 0.5, w: w * 0.5, h: h * 0.15, fill: { color: ICE_BLUE }, line: { type: 'none' } });
  slide.addShape('rect', { x: x - size * 0.05, y: y + h * 0.65, w: size * 0.05, h: h * 0.3, fill: { color: accent }, line: { type: 'none' } });
  slide.addText(label, { x, y: y + h + size * 0.03, w, h: size * 0.14, fontFace: 'Calibri', fontSize: Math.max(7, size * 10), bold: true, color, align: 'center' });
}

/** WNIC: NIC card + wireless signal arcs — same as a NIC but with an antenna signal, labelled WNIC (not NIC) since it represents the wireless variant specifically. */
function wnicIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  nicIcon(slide, { x, y, size, color, accent, label: 'WNIC' });
  const cx = x + size * 0.75 * 0.6, cy = y - size * 0.06;
  const sw = strokeWidth(size, 1.4, 1);
  // three concentric arcs centred on the same point, like a standard wireless-signal glyph
  [0.12, 0.2, 0.28].forEach((r) => {
    slide.addShape('blockArc', {
      x: cx - size * r, y: cy - size * r, w: size * r * 2, h: size * r * 2,
      angleRange: [200, 340],
      arcThickness: 'sm',
      fill: { type: 'none' }, line: { color: accent, width: sw * 0.8 },
    });
  });
}

/**
 * Cable: a coiled/zig-zag cable run with a connector plug at each end —
 * generic "wired transmission medium" glyph, added for Chapter 2 Lesson 3
 * (transmission media) so wired-cable content doesn't have to reuse an
 * unrelated icon (e.g. cloud) purely for lack of a purpose-built one.
 */
function cableIcon(slide, { x, y, size = 1, color = NAVY, accent = AMBER } = {}) {
  const sw = strokeWidth(size, 1.6, 1.2);
  const y0 = y + size * 0.5;
  // zig-zag cable body
  const pts = [0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0];
  for (let i = 0; i < pts.length - 1; i++) {
    const x1 = x + size * (0.08 + pts[i] * 0.84);
    const x2 = x + size * (0.08 + pts[i + 1] * 0.84);
    const y1 = y0 + (i % 2 === 0 ? -1 : 1) * size * 0.1;
    const y2 = y0 + ((i + 1) % 2 === 0 ? -1 : 1) * size * 0.1;
    slide.addShape('line', { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), line: { color, width: sw }, flipV: y2 < y1 });
  }
  // connector plugs at each end
  slide.addShape('rect', { x: x, y: y0 - size * 0.09, w: size * 0.1, h: size * 0.18, fill: { color: accent }, line: { color, width: 1 } });
  slide.addShape('rect', { x: x + size * 0.9, y: y0 - size * 0.09, w: size * 0.1, h: size * 0.18, fill: { color: accent }, line: { color, width: 1 } });
}

module.exports = {
  storageDrive, keyboard, globe, hexSwatch, sevenSegmentDisplay, cpu, padlock, cloud,
  deviceBox, hubIcon, switchIcon, repeaterIcon, bridgeIcon, routerIcon, gatewayIcon, modemIcon, nicIcon, wnicIcon,
  cableIcon,
  NAVY, NAVY_DARK, ICE_BLUE, WHITE, AMBER, strokeWidth,
};
