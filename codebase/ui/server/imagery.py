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
import sys
import time
import urllib.error
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
                 r"|chart|graph|plot|survey|statistic|histogram|infographic)", re.I)


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


# Commons is a donated service and asks to be treated like one: one modest backoff on a
# "come back later", never a hammering loop.
RETRY_ON = frozenset({429, 500, 502, 503, 504})
_last_error: str | None = None


def last_error() -> str | None:
    """Why the most recent download() gave up, or None if it succeeded.

    A caller that only sees None cannot tell "the picture is not there" from "the server
    refused us", and those two want different words on screen.
    """
    return _last_error


def _refused(why: str) -> None:
    """Record a download failure and say it out loud rather than returning a bare None."""
    global _last_error
    _last_error = why
    print("imagery: tải ảnh thất bại — %s" % why, file=sys.stderr)


def _host(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc or "máy chủ ảnh"


def download(url: str, out, tries: int = 3) -> Path | None:
    """Fetch one Commons image to `out`. Returns the path, or None with a stated reason.

    `out` may be a str or a Path. It used to be handed straight to `Path.write_bytes`,
    so a str caller raised AttributeError, the bare `except Exception` swallowed it, and
    every hit looked like a picture that would not download — for files upload.wikimedia
    was serving with a plain 200. A wrong TYPE is the caller's bug, so coercing it here
    is the whole fix; anything genuinely unusable is now named instead of hidden.

    The descriptive User-Agent goes on the IMAGE request too, not only on api.php:
    Wikimedia answers a UA-less fetch with 403. 429 and 5xx get a short backoff and are
    reported as a refusal, which is not the same thing as no picture existing.
    """
    global _last_error
    dest = Path(out)  # deliberately outside the try: a bad type is a bug, not a 404
    _last_error = None
    body: bytes | None = None
    kind = ""

    for attempt in range(1, max(1, tries) + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "image/*,*/*;q=0.5",
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                kind = (r.headers.get("Content-Type") or "").split(";")[0].strip()
                body = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code in RETRY_ON and attempt < tries:
                wait = float(e.headers.get("Retry-After") or 0) or 1.5 * attempt
                time.sleep(min(wait, 8.0))
                continue
            _refused("%s trả về HTTP %d %s" % (_host(url), e.code, e.reason))
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < tries:
                time.sleep(1.5 * attempt)
                continue
            _refused("không kết nối được %s (%s)" % (_host(url), e))
            return None

    if body is None:
        _refused("%s không trả lời sau %d lần thử" % (_host(url), tries))
        return None
    if not kind.startswith("image/"):
        # A captcha or an error page written to disk would sail past cover() and land a
        # wall of HTML-shaped noise behind a caption.
        _refused("%s trả về %s chứ không phải ảnh" % (_host(url), kind or "không rõ kiểu"))
        return None

    dest.write_bytes(body)
    try:
        with Image.open(dest) as im:
            im.verify()
    except Exception as e:
        dest.unlink(missing_ok=True)
        _refused("%d byte từ %s không mở được thành ảnh (%s)" % (len(body), _host(url), e))
        return None
    return dest


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

def treat(img, blur: float = 1.6, tint=(10, 59, 117), strength: float = 0.34):
    """Make a photograph behave as a background instead of competing as a picture.

    A sharp, full-colour photograph behind a sentence pulls the eye off the words, and
    eight unrelated photographs make a deck look like a stock-image catalogue. A light
    blur and a pull toward the brand navy keeps every card recognisably the same film,
    and gives the scrim less work to do.
    """
    from PIL import ImageEnhance, ImageFilter
    out = img.convert("RGB")
    if blur > 0:
        out = out.filter(ImageFilter.GaussianBlur(blur))
    out = ImageEnhance.Color(out).enhance(0.72)
    wash = Image.new("RGB", out.size, tuple(tint))
    return Image.blend(out, wash, max(0.0, min(0.85, strength)))
