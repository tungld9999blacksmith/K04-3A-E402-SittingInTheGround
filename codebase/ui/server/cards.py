"""Card renderer for lecture video frames.

Each card is a 1920x1080 keyframe designed for readability on high-resolution displays
and projectors. High contrast, strict margin safety, and measured text wrapping ensure
Vietnamese diacritics never overflow or clip.
"""

from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NAVY = (10, 59, 117)
NAVY_DEEP = (7, 42, 84)
GOLD = (214, 162, 30)
PAPER = (246, 247, 250)
BODY = (214, 226, 242)
MUTED = (150, 172, 200)

FONT_DIR = Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts"


def _font(size: int, bold: bool = False):
    # Prefer Segoe UI for Vietnamese diacritics kerning, then Arial, before PIL default.
    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        path = FONT_DIR / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _break_token(draw: ImageDraw.ImageDraw, word: str, font, max_w: int) -> list[str]:
    """Split a token that fits on no line at all, such as a full source address.

    Without this the oversized word is accepted whole and runs off the side of the frame,
    and the closing card is nothing but addresses, so it is the card that would break.
    """
    out, piece = [], ""
    for ch in word:
        if piece and draw.textlength(piece + ch, font=font) > max_w:
            out.append(piece)
            piece = ch
        else:
            piece += ch
    if piece:
        out.append(piece)
    return out


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    # Vietnamese tone marks distort character count; wrap only on actual rendered length.
    if not (text or "").strip():
        return []
    lines: list[str] = []
    # A line break in the text is a real break. The closing card passes a list of sources,
    # and reflowing it as one paragraph runs the entries into each other.
    for para in (text or "").strip().splitlines():
        words = para.split()
        if not words:
            continue
        line = ""
        for word in words:
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=font) <= max_w:
                line = trial
                continue
            if line:
                lines.append(line)
                line = ""
            if draw.textlength(word, font=font) > max_w:
                chunks = _break_token(draw, word, font, max_w)
                lines.extend(chunks[:-1])
                line = chunks[-1] if chunks else ""
            else:
                line = word
        if line:
            lines.append(line)
    return lines


def _fit_title(draw: ImageDraw.ImageDraw, text: str, max_w: int):
    # Step down title size dynamically to avoid truncation while staying prominent.
    for size in range(92, 36, -4):
        font = _font(size, bold=True)
        lines = _wrap(draw, text, font, max_w)
        if len(lines) <= 3:
            return lines, font, size
    font = _font(36, bold=True)
    return _wrap(draw, text, font, max_w)[:3], font, 36


def _fit_caption(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_lines: int = 4,
                 avail_h: int | None = None):
    """Largest size at which the caption fits both the line budget and the space left.

    A card that is a list rather than a sentence asks for more lines, and takes smaller
    type to hold them; either way it must end above the footer.
    """
    def fits(lines, size):
        if len(lines) > max_lines:
            return False
        return avail_h is None or len(lines) * int(size * 1.38) <= avail_h

    for size in (42, 38, 34, 30, 26, 22, 20, 18):
        font = _font(size, bold=False)
        lines = _wrap(draw, text, font, max_w)
        if fits(lines, size):
            return lines, font, size
    # Nothing fits cleanly: keep the type readable and drop what will not fit, rather
    # than drawing over the footer.
    font = _font(18, bold=False)
    lines = _wrap(draw, text, font, max_w)
    room = max_lines if avail_h is None else min(max_lines, max(1, avail_h // int(18 * 1.38)))
    return lines[:room], font, 18


def card(size=(1920, 1080), bg=None, eyebrow=None, title="", caption="",
         footer_left="", footer_right="", accent=None, caption_lines=4) -> Image.Image:
    w, h = size
    accent_color = accent or GOLD

    if bg is not None:
        base = (bg.resize((w, h)) if bg.size != (w, h) else bg.copy()).convert("RGBA")
        # The scrim has to be measured, not guessed. A fixed ramp that tames a dark
        # photograph leaves a near-white one bright enough that its own lettering reads
        # as loudly as ours, and the card becomes two slides stacked. So work out how
        # bright this picture actually is and hold the composite down to a floor.
        small = base.convert("L").resize((16, 9))
        px = list(small.getdata())
        lum = max(sum(px) / len(px), max(px[:32] or [0]) * 0.75)
        want, ink = 52.0, 22.0          # target luminance, and the scrim's own
        a = 0.55 if lum <= want else (lum - want) / max(lum - ink, 1.0)
        a = min(max(a, 0.55), 0.90)     # never fully bury the picture
        scrim = Image.new("RGBA", (w, h))
        sd = ImageDraw.Draw(scrim)
        for y in range(h):
            # Stronger density at bottom guards captions and metadata.
            f = min(a + 0.06 * (y / h), 0.94)
            sd.line([(0, y), (w, y)], fill=(7, 25, 55, int(round(255 * f))))
        base.alpha_composite(scrim)
        img = base.convert("RGB")
    else:
        # Vertical gradient keeps uniform cards visually rich without distraction.
        img = Image.new("RGB", (w, h), NAVY)
        d = ImageDraw.Draw(img)
        for y in range(h):
            t = y / h
            col = tuple(int(NAVY[i] + (NAVY_DEEP[i] - NAVY[i]) * t) for i in range(3))
            d.line([(0, y), (w, y)], fill=col)
        # A smooth gradient is the same picture at every zoom level, so the camera push
        # would be invisible on any card that has no photograph — and those are common,
        # because a licensed, on-topic picture often does not exist. Faint structure
        # gives the eye something to measure the movement against. It stays well below
        # the typography: a lattice this dim reads as texture, never as content.
        step = 72
        for gy in range(step // 2, h, step):
            t = gy / h
            base = tuple(int(NAVY[i] + (NAVY_DEEP[i] - NAVY[i]) * t) for i in range(3))
            dot = tuple(min(255, c + 13) for c in base)
            for gx in range(step // 2, w, step):
                d.ellipse([gx - 2, gy - 2, gx + 2, gy + 2], fill=dot)
        ring = tuple(min(255, c + 9) for c in NAVY_DEEP)
        for r in (430, 700, 980):
            d.ellipse([w - 330 - r, h - 120 - r, w - 330 + r, h - 120 + r],
                      outline=ring, width=3)

    d = ImageDraw.Draw(img)
    # Left accent spine anchors the frame across transitions.
    d.rectangle([0, 0, 14, h], fill=accent_color)

    max_w = w - 260
    FOOT_Y = h - 130
    has_eyebrow = bool(eyebrow and eyebrow.strip())

    if has_eyebrow:
        # Tracked uppercase gives section tags an editorial feel.
        eb_font = _font(28, bold=True)
        eb_x = 130
        for ch in eyebrow.strip().upper():
            d.text((eb_x, 100), ch, font=eb_font, fill=MUTED)
            eb_x += d.textlength(ch, font=eb_font) + 4

    title_clean, caption_clean = (title or "").strip(), (caption or "").strip()
    title_lines, title_font, title_size = (_fit_title(d, title_clean, max_w) if title_clean else ([], None, 92))

    # Offset title vertically to balance remaining card density.
    if len(title_lines) >= 3:
        y = 230 if has_eyebrow else 250
    elif len(title_lines) == 2:
        y = 260 if has_eyebrow else 280
    else:
        y = 290 if has_eyebrow else 300

    for ln in title_lines:
        d.text((130, y), ln, font=title_font, fill=PAPER)
        y += int(title_size * 1.22)

    rule_y = y + 24
    if title_lines and caption_clean:
        cap_top = rule_y + 36
    elif caption_clean:
        cap_top = 260
    else:
        cap_top = y

    # The caption is fitted against the room actually left above the footer, not against
    # a line count. A six-entry source list once ran straight through the footer row:
    # a block can sit inside every margin and still collide with the line below it.
    avail_h = (FOOT_Y - 30) - cap_top
    cap_lines, cap_font, cap_size = (
        _fit_caption(d, caption_clean, max_w, caption_lines, avail_h) if caption_clean
        else ([], None, 42))

    if title_lines and cap_lines:
        # Rule provides visual separation between headline and spoken sentences.
        d.rectangle([130, rule_y, 270, rule_y + 6], fill=accent_color)

    y = cap_top
    for ln in cap_lines:
        d.text((130, y), ln, font=cap_font, fill=BODY)
        y += int(cap_size * 1.38)

    # Footer stays safely above 40px broadcast overscan band and sample line.
    foot_font = _font(30)
    foot_y = FOOT_Y

    if footer_left and footer_left.strip():
        d.text((130, foot_y), footer_left.strip(), font=foot_font, fill=MUTED)

    if footer_right and footer_right.strip():
        fr = footer_right.strip()
        d.text((w - 130 - d.textlength(fr, font=foot_font), foot_y), fr, font=foot_font, fill=MUTED)

    return img
