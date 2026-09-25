"""Locate external tools (poppler, LibreOffice, Node) the same way in every script.

Why: Git for Windows ships an old xpdf `pdftotext`/`pdftoppm` in its mingw64\\bin folder, and it can
sit ahead of poppler on PATH. The xpdf versions lack options we use (e.g. `pdftotext -bbox`), so a
plain PATH lookup can silently pick the wrong program. Poppler is therefore looked up first in
POPPLER_BIN (if set), then in C:\\poppler\\*\\Library\\bin, and only then on PATH, skipping Git's copy.
"""
import glob
import os
import shutil


def _poppler(name):
    dirs = [os.environ.get("POPPLER_BIN", "")] + sorted(glob.glob(r"C:\poppler\*\Library\bin"), reverse=True) \
        + [r"C:\poppler\Library\bin"]
    for d in dirs:
        exe = os.path.join(d, name + ".exe")
        if d and os.path.exists(exe):
            return exe
    found = shutil.which(name)
    if found and "\\git\\" not in found.lower():
        return found
    raise SystemExit(f"{name} (poppler) not found: install poppler (see README) or set POPPLER_BIN")


PDFTOTEXT = _poppler("pdftotext")
PDFTOPPM = _poppler("pdftoppm")
PDFIMAGES = _poppler("pdfimages")
SOFFICE = shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.com"
NODE = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
