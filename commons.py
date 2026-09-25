"""Find, credit and download Wikimedia Commons images for lessons.

Usage:
  python commons.py search "hard disk head" [--limit 20]    text search (files)
  python commons.py category "Category:EPROM" [--limit 40]  files in a Commons category
  python commons.py info "File:A.jpg" ["File:B.jpg" ...]     licence, author, size + ready lines
  python commons.py fetch <content.md>                       list images still to download
  python commons.py fetch <content.md> --yes                 download them (after approval)

In content.md, an image from Commons is written as:
  image: assets/hdd_head_jd92.jpg
  credit: "Cabezal Lector de Disco Duro.JPG" by Jd92, Wikimedia Commons, CC BY-SA 3.0, https://...
  source: commons File:Cabezal_Lector_de_Disco_Duro.JPG
`info` prints those three lines ready to paste. `fetch` downloads every image whose source is
Commons and whose file does not exist yet: a 1280 px version (or the original if smaller),
paced 5 s apart with retries, because Wikimedia refuses bursts of requests (HTTP 429).
The User-Agent names the tool only; no personal details are sent.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "lesson-build/1.0 (classroom slide builder)"}
WIDTH = 1280
PAUSE = 5


def get(url, method="GET", tries=4):
    for attempt in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA, method=method), timeout=60)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            time.sleep(15 * (attempt + 1))


def api(**params):
    params.update(action="query", format="json", formatversion="2")
    return json.load(get(API + "?" + urllib.parse.urlencode(params)))


def strip_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


IMAGEINFO = dict(prop="imageinfo", iiprop="size|url|extmetadata", iiurlwidth=str(WIDTH),
                 iiextmetadatafilter="LicenseShortName|Artist|Credit|ImageDescription")


def describe(page):
    ii = (page.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata", {})
    title = page["title"]
    name = title.split(":", 1)[1]
    licence = strip_html(meta.get("LicenseShortName", {}).get("value", "unknown licence"))
    artist = strip_html(meta.get("Artist", {}).get("value", "")) or strip_html(meta.get("Credit", {}).get("value", "unknown"))
    small = ii.get("width", 0) <= WIDTH
    return {
        "title": title, "name": name, "width": ii.get("width"), "height": ii.get("height"),
        "licence": licence, "artist": artist,
        "description": strip_html(meta.get("ImageDescription", {}).get("value", ""))[:120],
        "download": (ii.get("url") if small else ii.get("thumburl", ii.get("url", ""))).split("?")[0],
        "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"), safe=":()"),
    }


def credit_line(d):
    who = f" by {d['artist']}" if d["artist"] and d["artist"] != "unknown" else ""
    return f"\"{d['name']}\"{who}, Wikimedia Commons, {d['licence']}, {d['page']}"


def show(pages):
    rows = [describe(p) for p in pages if "imageinfo" in p]
    for d in rows:
        print(f"{d['title']}\n    {d['width']}x{d['height']} | {d['licence']} | {d['artist'][:60]}\n    {d['description']}")
    print(f"\n{len(rows)} files")


def info(titles):
    pages = api(titles="|".join(titles), **IMAGEINFO)["query"]["pages"]
    for p in pages:
        if p.get("missing"):
            print(f"{p['title']}: NOT FOUND\n")
            continue
        d = describe(p)
        print(f"{d['title']}  ({d['width']}x{d['height']}, {d['licence']})")
        print(f"  credit: {credit_line(d)}")
        print(f"  source: commons {d['title'].replace(' ', '_')}\n")


def wanted(content_path):
    """(image path, source title, credit) for every Commons image in content.md."""
    base = os.path.dirname(os.path.abspath(content_path))
    text = open(content_path, encoding="utf-8-sig").read()
    out = []
    for block in re.split(r"\n(?=##+ )", text):
        img = re.search(r"^image:\s*(.+)$", block, re.M)
        src = re.search(r"^source:\s*commons\s+(File:.+)$", block, re.M)
        cred = re.search(r"^credit:\s*(.+)$", block, re.M)
        if img and src:
            out.append((os.path.normpath(os.path.join(base, img.group(1).strip())), src.group(1).strip(),
                        cred.group(1).strip() if cred else ""))
    return out


def fetch(content_path, yes):
    todo = [w for w in wanted(content_path) if not os.path.exists(w[0])]
    if not todo:
        print("All Commons images in this content.md are already downloaded.")
        return
    pages = {p["title"].replace(" ", "_"): p for p in
             api(titles="|".join(t for _, t, _ in todo), **IMAGEINFO)["query"]["pages"]}
    print(f"{'Save as':<40} {'Licence':<14} {'Size':>8}  Source")
    plan = []
    for path, title, credit in todo:
        p = pages.get(title.replace(" ", "_"))
        if not p or p.get("missing"):
            print(f"{os.path.basename(path):<40} NOT FOUND on Commons: {title}")
            continue
        d = describe(p)
        time.sleep(PAUSE)
        size = int(get(d["download"], "HEAD").headers.get("Content-Length", 0))
        warn = "" if d["licence"] in credit else f"   <- credit line does not mention {d['licence']}"
        print(f"{os.path.basename(path):<40} {d['licence']:<14} {size // 1024:>5} KB  {d['page']}{warn}")
        plan.append((path, d))
    if not yes:
        print("\nNothing downloaded. After approval, run again with --yes.")
        return
    from PIL import Image
    for path, d in plan:
        time.sleep(PAUSE)
        data = get(d["download"]).read()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            print(f"saved {os.path.basename(path)}: {len(data) // 1024} KB, {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    a = sys.argv[1:]
    lim = int(a[a.index("--limit") + 1]) if "--limit" in a else 20
    if not a:
        sys.exit(__doc__)
    if a[0] == "search":
        show(api(generator="search", gsrsearch=a[1], gsrnamespace="6", gsrlimit=str(lim), **IMAGEINFO)
             .get("query", {}).get("pages", []))
    elif a[0] == "category":
        show(api(generator="categorymembers", gcmtitle=a[1], gcmtype="file", gcmlimit=str(lim), **IMAGEINFO)
             .get("query", {}).get("pages", []))
    elif a[0] == "info":
        info(a[1:])
    elif a[0] == "fetch":
        fetch(a[1], "--yes" in a)
    else:
        sys.exit(__doc__)
