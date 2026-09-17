"""Pictures for the cards, from a place that lets us use them.

Wikimedia Commons, not a web image search: every file there carries a licence and an
author, which is the only kind of picture a lesson about checking your sources has any
business putting on screen. No API key, no account.

When Commons has nothing for a topic, the card falls back to a generated background
rather than an unlicensed photograph.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
UA = "ScriptScout/0.1 (VinUni course project; contact via repo)"
# Behind a caption, anything that carries its own lettering is a competing slide,
# not a background: a survey bar chart once landed under a Kubernetes card and both
# layers of type fought. Photographs and scenes only.
BAD = re.compile(r"(logo|icon|flag|coat[_ ]of[_ ]arms|signature|barnstar|\.svg$"
                 r"|chart|graph|plot|survey|statistic|histogram|infographic"
                 r"|screenshot|slide|diagram|table|timeline|poster|results?\b)", re.I)


def _get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def find(query: str, want: int = 1) -> list[dict]:
    """Search Commons for photographs or diagrams about a topic.

    Returns {url, author, licence, title} per hit. Logos, flags and icons are filtered
    out: they make a card look like a brochure rather than a lesson.
    """
    try:
        data = _get({
            "action": "query",
            "generator": "search",
            "gsrsearch": "filetype:bitmap " + query,
            "gsrnamespace": "6",
            "gsrlimit": str(max(6, want * 4)),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size",
            "iiurlwidth": "1920",
        })
    except Exception:
        return []

    out: list[dict] = []
    for page in (data.get("query") or {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        src = info.get("thumburl") or info.get("url")
        title = page.get("title", "")
        if not src or BAD.search(title):
            continue
        if (info.get("width") or 0) < 800:
            continue
        meta = info.get("extmetadata") or {}

        def field(key: str) -> str:
            raw = (meta.get(key) or {}).get("value") or ""
            return re.sub(r"<[^>]+>", "", raw).strip()

        out.append({
            "url": src,
            "title": re.sub(r"^File:|\.[a-z]+$", "", title),
            "author": field("Artist") or field("Credit") or "Wikimedia Commons",
            "licence": field("LicenseShortName") or "xem Commons",
        })
        if len(out) >= want:
            break
    return out


def download(url: str, out: Path) -> Path | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            out.write_bytes(r.read())
        return out
    except Exception:
        return None


def cover(path: Path, size: tuple[int, int]):
    """Crop to fill the frame without squashing anything."""
    from PIL import Image

    img = Image.open(path).convert("RGB")
    tw, th = size
    scale = max(tw / img.width, th / img.height)
    img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))),
                     Image.LANCZOS)
    left = (img.width - tw) // 2
    top = (img.height - th) // 2
    return img.crop((left, top, left + tw, top + th))

def is_flat_document(path) -> bool:
    """True for a chart, slide or screenshot: mostly blank paper with a little ink.

    The titles are no help — Wikimedia's own survey charts are filed as "2023-12 DSS
    deployment kubernetes satisfaction", with no word a filter could catch. The pixels
    give it away instead: a document is a large expanse of near-white at almost no
    saturation, which no photograph of a real scene ever is.
    """
    try:
        with Image.open(path) as im:
            small = im.convert("RGB").resize((64, 36))
    except Exception:
        return False
    px = list(small.getdata())
    pale = sum(1 for r, g, b in px if min(r, g, b) > 228) / len(px)
    grey = sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) < 18) / len(px)
    return pale > 0.30 and grey > 0.60
