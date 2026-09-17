"""Turn an approved script into an actual video file, locally, with no video model.

Text and graphics, which is what a lecture video is: one card per sentence, narrated by a
free Vietnamese voice, stitched with ffmpeg. Nothing here calls a paid generative service,
so a three minute lesson costs nothing and takes about as long as the audio it contains.

Two choices worth defending:

  * every card carries the source ids for the sentence being spoken. The whole product is
    that a claim can be traced, and a video that drops the provenance on the way out
    throws away the only thing that made it worth checking;
  * the last card is the source list. The video ends by showing its own bibliography.

Requires nothing on the system: ffmpeg arrives with imageio-ffmpeg inside the venv, the
voice comes from edge-tts, and the font is the one Windows already has.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import textwrap
from pathlib import Path

W, H = 1920, 1080
NAVY = (10, 59, 117)
NAVY_DEEP = (7, 42, 84)
GOLD = (214, 162, 30)
RED = (163, 29, 36)
PAPER = (246, 247, 250)
MUTED = (150, 172, 200)

VOICES = {"nu": "vi-VN-HoaiMyNeural", "nam": "vi-VN-NamMinhNeural"}
FONT_DIR = Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts"


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        path = FONT_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args: list[str]) -> None:
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        tail = (p.stderr or "").strip().splitlines()[-4:]
        raise RuntimeError("ffmpeg lỗi: " + " / ".join(tail))


# ---------------------------------------------------------------- cards

def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    """Wrap on real measured width, not a character count: Vietnamese diacritics make
    character counting lie by a wide margin."""
    words = (text or "").split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _base(title: str | None = None):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    # A quiet vertical gradient so the card does not read as flat colour on a projector.
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(
            int(NAVY[0] + (NAVY_DEEP[0] - NAVY[0]) * t),
            int(NAVY[1] + (NAVY_DEEP[1] - NAVY[1]) * t),
            int(NAVY[2] + (NAVY_DEEP[2] - NAVY[2]) * t),
        ))
    d.rectangle([0, 0, 14, H], fill=GOLD)
    if title:
        d.text((90, 66), title.upper(), font=_font(30, True), fill=MUTED)
    return img, d


def display_title(brief: dict) -> str:
    """The brief is whatever the reviewer typed, which is a request, not a title.

    "Giải thích DNS cho sinh viên năm nhất, video ba mươi giây, các em chưa biết gì về
    mạng" is a fine thing to say and a terrible thing to put on a title card. Take the
    first clause and drop the production notes.
    """
    raw = (brief.get("topic") or brief.get("raw") or "Kịch bản bài giảng").strip()
    head = re.split(r"[,;.]", raw)[0].strip() or raw
    head = re.sub(r"^(giải thích|dạy|nói về|trình bày)\s+", "", head, flags=re.I)
    head = re.sub(r"\s+(video|thời lượng)\s.*$", "", head, flags=re.I)
    head = (head[:80].strip() or raw[:80])
    # Only lift the first letter. capitalize() lowercases the rest and turns DNS into Dns.
    return head[:1].upper() + head[1:] if head else "Kịch bản bài giảng"


def title_card(path: Path, brief: dict, total: float, sentences: int) -> None:
    img, d = _base()
    topic = display_title(brief)
    f = _font(84, True)
    lines = _wrap(d, topic, f, W - 260)[:4]
    y = 300
    for ln in lines:
        d.text((130, y), ln, font=f, fill=PAPER)
        y += 104
    d.rectangle([130, y + 30, 330, y + 38], fill=GOLD)
    meta = "%d câu · %d giây · bản nháp cần người duyệt" % (sentences, round(total))
    d.text((130, y + 90), meta, font=_font(38), fill=MUTED)
    learners = brief.get("learners")
    if learners:
        d.text((130, y + 150), "Người học: " + learners, font=_font(34), fill=MUTED)
    img.save(path)


def sentence_card(path: Path, row: dict, section: str, index: int, count: int,
                  source_ids: list[str]) -> None:
    img, d = _base(section)

    chu = (row.get("chu") or "").strip()
    f_chu = _font(96, True)
    lines = _wrap(d, chu, f_chu, W - 260)[:3]
    y = 250 if len(lines) > 1 else 300
    for ln in lines:
        d.text((130, y), ln, font=f_chu, fill=PAPER)
        y += 118

    d.rectangle([130, y + 24, 260, y + 31], fill=GOLD)

    f_loi = _font(42)
    for ln in _wrap(d, row.get("loi") or "", f_loi, W - 300)[:4]:
        y += 84
        d.text((130, y + 24), ln, font=f_loi, fill=(214, 226, 242))

    # Provenance stays on screen. A video that drops it is just a video.
    foot = _font(32)
    label = ("Nguồn: " + ", ".join(source_ids)) if source_ids else "Câu chuyển, không cần nguồn"
    d.text((130, H - 110), label, font=foot, fill=GOLD if source_ids else MUTED)
    counter = "%d / %d" % (index, count)
    d.text((W - 130 - d.textlength(counter, font=foot), H - 110), counter, font=foot, fill=MUTED)
    img.save(path)


def sources_card(path: Path, sources: dict, used: set[str]) -> None:
    img, d = _base("Hồ sơ nguồn")
    f = _font(60, True)
    d.text((130, 200), "Các nguồn đã dùng", font=f, fill=PAPER)
    d.rectangle([130, 296, 330, 303], fill=GOLD)

    fid, ftx = _font(32, True), _font(32)
    y = 360
    for sid in sorted(used):
        s = sources.get(sid) or {}
        if y > H - 190:
            break
        d.text((130, y), sid, font=fid, fill=GOLD)
        text = "%s — %s" % (s.get("url", ""), {"cao": "tin cậy cao",
                                               "trungbinh": "tin cậy trung bình",
                                               "thap": "tin cậy thấp"}.get(s.get("trust"), s.get("trust") or ""))
        for ln in _wrap(d, text, ftx, W - 420)[:1]:
            d.text((240, y), ln, font=ftx, fill=(214, 226, 242))
        y += 58
    d.text((130, H - 130), "Bản nháp do người duyệt chốt, chưa phải bản phát hành.",
           font=_font(30), fill=MUTED)
    img.save(path)


# ---------------------------------------------------------------- voice

async def _speak(text: str, voice: str, out: Path) -> None:
    import edge_tts

    await edge_tts.Communicate(text, voice).save(str(out))


def speak(text: str, voice: str, out: Path) -> None:
    # Strip anything a narrator should not read aloud.
    clean = re.sub(r"\s+", " ", (text or "").strip())
    asyncio.run(_speak(clean or "…", voice, out))


def silence(seconds: float, out: Path) -> None:
    run([ffmpeg_exe(), "-y", "-v", "error", "-f", "lavfi",
         "-i", "anullsrc=channel_layout=stereo:sample_rate=24000",
         "-t", "%.2f" % seconds, str(out)])


# ---------------------------------------------------------------- assembly

def clip(image: Path, audio: Path, out: Path) -> None:
    run([ffmpeg_exe(), "-y", "-v", "error",
         "-loop", "1", "-i", str(image), "-i", str(audio),
         "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-r", "24",
         "-c:a", "aac", "-b:a", "128k", "-ar", "24000",
         "-shortest", "-movflags", "+faststart", str(out)])


def render(script: dict, claims: dict, sources: dict, brief: dict, outdir: Path,
           voice: str = "nu", on_line=None) -> dict:
    """Build the video. Returns the path and what it contains."""
    def say(kind: str, text: str) -> None:
        if on_line:
            on_line(kind, text)

    outdir = Path(outdir)
    work = outdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    rows = script.get("sentences") or []
    if not rows:
        raise RuntimeError("Kịch bản rỗng, chưa dựng được.")

    sections = {s["no"]: s.get("name", "") for s in (script.get("sections") or [])}
    voice_id = VOICES.get(voice, VOICES["nu"])
    parts: list[Path] = []
    used: set[str] = set()

    total_est = sum(float(r.get("dur") or 0) for r in rows)
    say("ok", "Dựng %d thẻ hình, giọng %s" % (len(rows) + 2, voice_id.split("-")[-1]))

    # title
    tpng, taud, tclip = work / "t.png", work / "t.mp3", work / "c000.mp4"
    title_card(tpng, brief, total_est, len(rows))
    speak(display_title(brief), voice_id, taud)
    clip(tpng, taud, tclip)
    parts.append(tclip)
    say("ok", "Xong thẻ mở đầu")

    for i, row in enumerate(rows, start=1):
        ids: list[str] = []
        for cid in row.get("cls") or []:
            for e in (claims.get(cid) or {}).get("evidence") or []:
                if e.get("src") and e["src"] not in ids:
                    ids.append(e["src"])
        used.update(ids)

        png, aud, mp4 = work / f"s{i:03d}.png", work / f"s{i:03d}.mp3", work / f"c{i:03d}.mp4"
        sentence_card(png, row, sections.get(row.get("sec"), ""), i, len(rows), ids)
        speak(row.get("loi") or "", voice_id, aud)
        clip(png, aud, mp4)
        parts.append(mp4)
        say("ok", "Câu %d trên %d đã có tiếng và hình" % (i, len(rows)))

    # closing source list, held for a readable beat
    spng, saud, sclip = work / "z.png", work / "z.mp3", work / "c999.mp4"
    sources_card(spng, sources, used)
    speak("Các nguồn đã dùng cho kịch bản này.", voice_id, saud)
    clip(spng, saud, sclip)
    parts.append(sclip)
    say("ok", "Xong thẻ hồ sơ nguồn")

    listing = work / "parts.txt"
    # ffmpeg resolves concat entries against the LIST file's own directory, so a relative
    # path here becomes out/x/work/out/x/work/clip.mp4 and the render dies at the last step.
    listing.write_text("".join("file '%s'\n" % p.resolve().as_posix() for p in parts),
                       encoding="utf-8")
    out = outdir / "video.mp4"
    run([ffmpeg_exe(), "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(out)])

    size = out.stat().st_size
    say("ok", "Xong video, %.1f MB" % (size / 1e6))
    return {"path": str(out), "bytes": size, "cards": len(parts),
            "sources": sorted(used), "voice": voice_id}
