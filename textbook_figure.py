"""Crop a figure from the textbook PDF at print resolution.

Usage: python textbook_figure.py <pdf> <page> <x0> <y0> <x1> <y1> <out.png> [dpi]

The box is in 72-dpi pixel coordinates (1 px = 1 pt), read off a `pdftoppm -r 72` render of
the page. The page is rendered at <dpi> (default 300), cropped, and trimmed to its content
plus a small white margin. Vector figures come out sharp at any size this way; embedded
photos in the chapter PDF are only ~150 ppi, so prefer Commons for photographs.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from PIL import Image, ImageChops

PDFTOPPM = shutil.which("pdftoppm") or r"C:\poppler\poppler-26.09.0\Library\bin\pdftoppm.exe"


def main(pdf, page, x0, y0, x1, y1, out, dpi=300):
    scale = dpi / 72
    with tempfile.TemporaryDirectory() as tmp:
        stem = os.path.join(tmp, "p")
        subprocess.run([PDFTOPPM, "-png", "-r", str(dpi), "-f", str(page), "-l", str(page), "-singlefile", pdf, stem], check=True)
        im = Image.open(stem + ".png").convert("RGB")
        box = tuple(int(v * scale) for v in (x0, y0, x1, y1))
        fig = im.crop(box)
    # trim surrounding white, then add a uniform margin
    bg = Image.new("RGB", fig.size, (255, 255, 255))
    diff = ImageChops.difference(fig, bg).convert("L").point(lambda v: 255 if v > 12 else 0)
    bbox = diff.getbbox()
    if bbox:
        fig = fig.crop(bbox)
    pad = int(0.08 * dpi)
    framed = Image.new("RGB", (fig.width + 2 * pad, fig.height + 2 * pad), "white")
    framed.paste(fig, (pad, pad))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    framed.save(out, dpi=(dpi, dpi))
    print(f"{out}: {framed.width}x{framed.height}px")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], int(a[2]), *map(float, a[3:7]), a[7], int(a[8]) if len(a) > 8 else 300)
