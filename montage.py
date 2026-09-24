"""Tile rendered page JPEGs into contact sheets for visual QA.

Usage: python montage.py <jpg glob pattern> <out_prefix> [cols] [per_sheet]
Pages are ordered by the trailing page number that pdftoppm adds (name-<n>.jpg).
"""
import glob
import re
import sys
from PIL import Image, ImageDraw

src, prefix = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
per = int(sys.argv[4]) if len(sys.argv) > 4 else 6
files = sorted(glob.glob(src), key=lambda p: int(re.search(r"-(\d+)\.jpg$", p).group(1)))
for sheet, start in enumerate(range(0, len(files), per), 1):
    batch = [Image.open(f) for f in files[start:start + per]]
    w, h = batch[0].size
    rows = (len(batch) + cols - 1) // cols
    out = Image.new("RGB", (cols * (w + 10) + 10, rows * (h + 34) + 10), "white")
    d = ImageDraw.Draw(out)
    for i, im in enumerate(batch):
        x, y = 10 + (i % cols) * (w + 10), 10 + (i // cols) * (h + 34)
        d.text((x, y), f"page {start + i + 1}", fill="red")
        out.paste(im, (x, y + 14))
    path = f"{prefix}_{sheet}.jpg"
    out.save(path, quality=85)
    print(path)
