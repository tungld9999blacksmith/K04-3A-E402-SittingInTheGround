"""Turn an approved script into a video, locally, with no generative video model.

The technique is the one the large open-source pipelines settled on — MoneyPrinterTurbo
and its relatives: narration from a text-to-speech voice, a still per beat, a slow Ken
Burns camera so the frame is never static, and ffmpeg to stitch it. What differs here is
where the pictures come from and what the cards say.

  * Pictures come from Wikimedia Commons, which carries a licence and an author for every
    file, and a model vets them for relevance first. An irrelevant picture is worse than
    none: a lesson about checking your sources cannot put a shipping crane on screen
    because somebody searched for "container".
  * Cards name the publisher, not the internal id. "Nguồn: Stanford" is something a
    viewer can act on; "Nguồn: n01" is a note to ourselves. The ids, licences and full
    addresses go on the closing card, which is where anyone checking will look.

Nothing is installed on the machine: ffmpeg arrives inside the venv with imageio-ffmpeg,
the voice is edge-tts, the fonts are the ones Windows already has.

Layout lives in cards.py, the camera in motion.py, the picture search in imagery.py.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cards
import imagery
import motion

W, H = 1920, 1080
VOICES = {"nu": "vi-VN-HoaiMyNeural", "nam": "vi-VN-NamMinhNeural"}
TWO_PART = {"com.vn", "edu.vn", "gov.vn", "org.vn", "net.vn", "co.uk", "ac.uk", "com.au"}
STOP_SUB = {"www", "developer", "docs", "blog", "news", "web", "vi", "en", "m"}

# A domain label is not always the name people know. Oxford lives at ox.ac.uk, and an
# acronym title-cased into "Ieee" looks like a typo on a lecture card. Only well-known
# cases belong here; anything missing falls back to the domain label, which is honest.
ALIAS = {
    "ox": "Oxford", "cam": "Cambridge", "mit": "MIT", "harvard": "Harvard",
    "w3": "W3C", "ieee": "IEEE", "acm": "ACM", "arxiv": "arXiv", "nih": "NIH",
    "who": "WHO", "oecd": "OECD", "unesco": "UNESCO", "mozilla": "Mozilla",
    "aws": "AWS", "ibm": "IBM", "bbc": "BBC", "vnexpress": "VnExpress",
    "vietnamnet": "VietnamNet", "tuoitre": "Tuổi Trẻ", "moet": "Bộ Giáo dục",
    "github": "GitHub", "gitlab": "GitLab", "openai": "OpenAI", "youtube": "YouTube",
    "postgresql": "PostgreSQL", "kubernetes": "Kubernetes",
}


# ---------------------------------------------------------------- naming things

def publisher(src: dict) -> str:
    """A name a viewer recognises, from whatever the source record happens to carry.

    Prefer the organisation the page states. Otherwise fall back to the registrable domain
    with the suffix dropped, which turns stanford.edu into Stanford and kubernetes.io into
    Kubernetes. The internal id never appears here.
    """
    org = (src.get("org") or "").strip()
    if org and "." not in org and len(org) > 2:
        return org[:34]

    # Sources normally arrive with the scheme already stripped, but one that does not
    # would otherwise be labelled "Https:" on every card it appears on.
    url = re.sub(r"^[a-z][a-z0-9+.-]*://", "", (src.get("url") or "").strip(), flags=re.I)
    host = url.split("/")[0].lower()
    parts = [p for p in host.split(".") if p]
    if parts and parts[0] in ALIAS:      # aws.amazon.com is AWS, not Amazon
        return ALIAS[parts[0]]
    while len(parts) > 2 and parts[0] in STOP_SUB:
        parts = parts[1:]
    if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_PART:
        name = parts[-3]
    elif len(parts) >= 2:
        name = parts[-2]
    elif parts:
        name = parts[0]
    else:
        return "không rõ nguồn"
    if name in ALIAS:
        return ALIAS[name]
    name = re.sub(r"[-_]+", " ", name).strip()
    return (name[:1].upper() + name[1:]) if name else "không rõ nguồn"


def display_title(brief: dict) -> str:
    """The brief is what the reviewer typed, which is a request, not a title.

    "Giải thích DNS cho sinh viên năm nhất, video ba mươi giây, các em chưa biết gì về
    mạng" is a fine thing to ask for and a terrible thing to put on a title card.
    """
    raw = (brief.get("topic") or brief.get("raw") or "Kịch bản bài giảng").strip()
    head = re.split(r"[,;.]", raw)[0].strip() or raw
    head = re.sub(r"^(giải thích|dạy|nói về|trình bày)\s+", "", head, flags=re.I)
    head = re.sub(r"\s+(video|thời lượng)\s.*$", "", head, flags=re.I)
    head = head[:80].strip() or raw[:80]
    # Only lift the first letter: capitalize() would turn DNS into Dns.
    return (head[:1].upper() + head[1:]) if head else "Kịch bản bài giảng"


def sources_for(row: dict, claims: dict) -> list[str]:
    out: list[str] = []
    for cid in row.get("cls") or []:
        for e in (claims.get(cid) or {}).get("evidence") or []:
            if e.get("src") and e["src"] not in out:
                out.append(e["src"])
    return out


# ---------------------------------------------------------------- pictures

def visual_terms(topic: str, sections: list[dict], judge) -> dict:
    """Concrete English things to photograph, per section.

    Searching Wikimedia Commons for a Vietnamese section name returns nothing at all,
    which is why eight sections in a row fell back to a drawn card. Commons is an
    English-language archive of photographs of real things, so it has to be asked for a
    real thing: "data center server room" finds CERN's machine hall, where "Cụm và node"
    finds silence.
    """
    if judge is None:
        return {}
    try:
        out = judge(
            "Bài giảng về %r, gồm các phần: %s.\n"
            "Với MỖI phần, cho hai từ khoá TIẾNG ANH để tìm ẢNH CHỤP trên Wikimedia "
            "Commons. Phải là VẬT THỂ CÓ THỂ CHỤP ĐƯỢC, cụ thể, ví dụ "
            "'data center server room', 'fibre optic cable', 'university lecture hall'. "
            "KHÔNG dùng từ trừu tượng, không dùng tên khái niệm, không dùng biểu đồ."
            % (topic, ", ".join("%s:%s" % (x.get("no"), x.get("name") or "") for x in sections)),
            '{"terms": [{"sec": 1, "words": ["...", "..."]}]}',
        )
        return {int(r["sec"]): [w for w in (r.get("words") or []) if w][:2]
                for r in (out.get("terms") or []) if r.get("sec") is not None}
    except Exception:
        return {}


def choose_images(topic: str, sections: list[dict], work: Path, judge=None,
                  say=None) -> dict:
    """One vetted picture per section, or none for that section.

    Commons keyword search is literal to a fault: "Docker container" returns cranes at
    Hamburg and "browser cache" returns a stone lion in Venice. So the candidates are
    described to a model, and it is allowed to answer that none of them fit — which is a
    better answer than a decorative wrong picture more often than not.
    """
    picked: dict = {}
    terms = visual_terms(topic, sections, judge)
    for sec in sections:
        no = sec.get("no")
        hits = []
        seen_titles = set()
        for query in (terms.get(no) or []) + [topic]:
            for h in imagery.find(query, want=4) or []:
                if h["title"] not in seen_titles:
                    seen_titles.add(h["title"])
                    hits.append(h)
            if len(hits) >= 6:
                break
        if not hits:
            continue

        keep = hits[0] if judge is None else None
        if judge is not None:
            try:
                verdict = judge(
                    "Bài giảng nói về %r, phần %r.\n"
                    "Dưới đây là tên các ảnh tìm được trên Wikimedia Commons. Chọn ảnh "
                    "THẬT SỰ minh hoạ đúng chủ đề. Tên ảnh nói về thứ khác, dù trùng từ "
                    "khoá, thì KHÔNG chọn. Không có ảnh nào phù hợp thì trả index = -1.\n\n"
                    % (topic, sec.get("name") or "")
                    + json.dumps([{"index": i, "title": h["title"]} for i, h in enumerate(hits)],
                                 ensure_ascii=False),
                    '{"index": 0, "why": "..."}',
                )
                idx = int(verdict.get("index", -1))
                keep = hits[idx] if 0 <= idx < len(hits) else None
            except Exception:
                keep = None

        if not keep:
            if say:
                say("caution", "Phần %s: không ảnh nào đúng chủ đề, dùng nền tự vẽ" % no)
            continue

        # Vetting by name is not enough, so each candidate is downloaded and looked at:
        # a chart or a screenshot is refused here even when the model liked its title.
        order = [keep] + [h for h in hits if h is not keep]
        for rank, cand in enumerate(order):
            raw = work / ("bg%02d_%d.img" % (no or 0, rank))
            if not imagery.download(cand["url"], raw):
                continue
            if imagery.is_flat_document(raw):
                if say:
                    say("caution", "Phần %s: %s là biểu đồ, không phải ảnh minh hoạ"
                        % (no, cand["title"][:38]))
                continue
            try:
                picked[no] = dict(cand, image=imagery.treat(imagery.cover(raw, (W, H))))
            except Exception:
                continue
            if say:
                say("ok", "Phần %s: ảnh %s, %s" % (no, cand["title"][:38], cand["licence"]))
            break
        else:
            if say:
                say("caution", "Phần %s: không có ảnh dùng được, dùng nền tự vẽ" % no)
    return picked


# ---------------------------------------------------------------- voice

async def _speak(text: str, voice: str, out: Path) -> None:
    import edge_tts

    await edge_tts.Communicate(text, voice).save(str(out))


WORDISH = re.compile(r"[0-9A-Za-zÀ-ỹ]")


def speak(text: str, voice: str, out: Path, seconds: float = 2.5) -> None:
    """Narrate the line, or lay down silence rather than bring the render down.

    Two things went wrong here in one run. A card with no spoken line fell back to "…",
    and the voice service answers punctuation with "No audio was received" — the render
    died on sentence two of thirty. And a network hiccup on any one line should cost that
    line its narration, not the whole film.
    """
    clean = re.sub(r"\s+", " ", (text or "").strip())
    if not WORDISH.search(clean):
        motion.silence(seconds, out)
        return
    try:
        asyncio.run(_speak(clean, voice, out))
        if Path(out).stat().st_size > 800:
            return
    except Exception:
        pass
    # Vietnamese runs about 2.9 syllables a second, which is close enough to word count
    # for a placeholder length.
    motion.silence(max(1.5, len(clean.split()) / 2.4), out)


# ---------------------------------------------------------------- the whole thing

def render(script: dict, claims: dict, sources: dict, brief: dict, outdir: Path,
           voice: str = "nu", on_line=None, judge=None) -> dict:
    def say(kind: str, text: str) -> None:
        if on_line:
            on_line(kind, text)

    outdir = Path(outdir)
    work = outdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    rows = script.get("sentences") or []
    if not rows:
        raise RuntimeError("Kịch bản rỗng, chưa dựng được.")

    sections = script.get("sections") or [{"no": 1, "name": ""}]
    names = {s["no"]: s.get("name", "") for s in sections}
    voice_id = VOICES.get(voice, VOICES["nu"])
    title = display_title(brief)

    say("ok", "Tìm ảnh có giấy phép trên Wikimedia Commons")
    backgrounds = choose_images(brief.get("topic") or title, sections, work,
                                judge=judge, say=say)

    parts: list[Path] = []
    used: set = set()
    total_est = sum(float(r.get("dur") or 0) for r in rows)

    # opening
    png, aud, clip = work / "c000.png", work / "c000.mp3", work / "c000.mp4"
    cards.card(bg=(backgrounds.get(sections[0].get("no")) or {}).get("image"),
               title=title,
               caption="%d câu · %d giây · bản nháp cần người duyệt"
                       % (len(rows), round(total_est)),
               footer_left=("Người học: " + brief["learners"]) if brief.get("learners") else "",
               footer_right="ScriptScout").save(png)
    speak(title, voice_id, aud)
    motion.ken_burns(str(png), str(aud), str(clip), zoom_in=True)
    parts.append(clip)
    say("ok", "Xong thẻ mở đầu")

    # one card per sentence
    for i, row in enumerate(rows, start=1):
        ids = sources_for(row, claims)
        used.update(ids)
        seen: list = []
        for sid in ids:
            label = publisher(sources.get(sid) or {})
            if label not in seen:
                seen.append(label)

        png = work / ("c%03d.png" % i)
        aud = work / ("c%03d.mp3" % i)
        clip = work / ("c%03d.mp4" % i)
        cards.card(bg=(backgrounds.get(row.get("sec")) or {}).get("image"),
                   eyebrow=names.get(row.get("sec"), ""),
                   title=(row.get("chu") or "").strip(),
                   caption=(row.get("loi") or "").strip(),
                   footer_left=("Nguồn: " + ", ".join(seen[:3])) if seen
                               else "Câu chuyển, không cần nguồn",
                   footer_right="%d / %d" % (i, len(rows))).save(png)
        speak(row.get("loi") or "", voice_id, aud, seconds=float(row.get("dur") or 2.5))
        motion.ken_burns(str(png), str(aud), str(clip), zoom_in=(i % 2 == 1))
        parts.append(clip)
        say("ok", "Câu %d trên %d: có tiếng, hình và chuyển động" % (i, len(rows)))

    # closing: who said what, with the ids for anyone checking
    lines = []
    for sid in sorted(used):
        s = sources.get(sid) or {}
        trust = {"cao": "tin cậy cao", "trungbinh": "tin cậy trung bình",
                 "thap": "tin cậy thấp"}.get(s.get("trust"), s.get("trust") or "")
        lines.append("%s · %s · %s · %s" % (publisher(s), s.get("url", ""), trust, sid))
    credits = [b["author"] + " · " + b["licence"] for b in backgrounds.values()]

    png, aud, clip = work / "c999.png", work / "c999.mp3", work / "c999.mp4"
    cards.card(title="Các nguồn đã dùng",
               caption="\n".join(lines[:6]) or "Chưa dùng nguồn nào.",
               caption_lines=10,
               footer_left=("Ảnh: " + "; ".join(credits))[:110] if credits else "",
               footer_right="bản nháp, chưa phát hành").save(png)
    speak("Các nguồn đã dùng cho kịch bản này.", voice_id, aud)
    motion.ken_burns(str(png), str(aud), str(clip), zoom_in=False)
    parts.append(clip)
    say("ok", "Xong thẻ hồ sơ nguồn")

    out = outdir / "video.mp4"
    motion.concat([str(p) for p in parts], str(out))
    size = out.stat().st_size
    seconds = motion.duration_of(str(out))
    say("ok", "Xong video, %.1f giây, %.1f MB" % (seconds, size / 1e6))
    return {"path": str(out), "bytes": size, "cards": len(parts),
            "seconds": round(seconds, 1), "sources": sorted(used), "voice": voice_id,
            "images": [{"title": b["title"], "author": b["author"], "licence": b["licence"]}
                       for b in backgrounds.values()]}
