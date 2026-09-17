"""The camera. A still plus narration in, a moving clip out.

A card that sits perfectly still for the length of its sentence reads as a dead
slideshow, however good the typography is. So every clip gets a slow Ken Burns push,
alternating direction card to card — always pushing the same way starts to feel like a
pulse. The move is small on purpose: enough that the frame is alive, not enough to
notice it happening.

ffmpeg is not installed on the machine. imageio-ffmpeg carries a binary inside the venv,
which is the whole reason this runs on a laptop with nothing set up.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()

ZOOM = 0.10       # ten percent across the whole clip; more than this looks like a lurch
FADE = 0.35
MIN_FADE = 1.2    # below this a fade pair eats most of the clip


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([FF] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _must(args: list[str], what: str) -> None:
    p = _run(args)
    if p.returncode != 0:
        tail = "\n".join((p.stderr or "").strip().splitlines()[-6:])
        raise RuntimeError("ffmpeg %s thất bại:\n%s" % (what, tail))


def duration_of(path) -> float:
    """Seconds, read from ffmpeg's own report. There is no ffprobe in the venv."""
    # No output file, so ffmpeg exits non-zero by design; the header is what we came for.
    out = _run(["-i", str(path)]).stderr or ""
    m = re.search(r"Duration:\s*(\d+):(\d\d):(\d\d\.\d+)", out)
    if not m:
        raise RuntimeError("Không đọc được thời lượng của %s" % path)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def ken_burns(image, audio, out, zoom_in: bool = True, fps: int = 24) -> float:
    """An mp4 exactly as long as the narration, with the frame never quite still."""
    dur = duration_of(audio)
    frames = max(2, round(dur * fps))

    # Zooming a 1920x1080 source to a 1920x1080 frame would just resample its own pixels,
    # so enlarge first and let the camera crop out of the bigger picture.
    ramp = ("1+%.4f*on/%d" % (ZOOM, frames)) if zoom_in \
        else ("%.4f-%.4f*on/%d" % (1 + ZOOM, ZOOM, frames))
    chain = [
        "scale=3840:2160:flags=lanczos",
        "setsar=1",
        "zoompan=z='%s':d=%d:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=%d"
        % (ramp, frames, fps),
    ]
    if dur >= MIN_FADE:
        chain.append("fade=t=in:st=0:d=%.2f" % FADE)
        chain.append("fade=t=out:st=%.3f:d=%.2f" % (dur - FADE, FADE))
    chain.append("format=yuv420p")

    _must(["-y", "-v", "error", "-loop", "1", "-i", str(image), "-i", str(audio),
           "-vf", ",".join(chain),
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(fps),
           "-c:a", "aac", "-b:a", "128k", "-ar", "24000",
           "-t", "%.3f" % dur, "-movflags", "+faststart", str(out)],
          "dựng clip")
    return dur


def concat(clips, out) -> None:
    """Join without re-encoding. Every clip already shares codec, size and frame rate."""
    paths = [Path(c) for c in clips]
    if not paths:
        raise RuntimeError("Không có clip nào để ghép.")
    listing = paths[0].parent / "concat.txt"
    # ffmpeg resolves each entry against the list file's own directory, so a relative
    # path here silently becomes a path that does not exist.
    listing.write_text(
        "".join("file '%s'\n" % p.resolve().as_posix() for p in paths), encoding="utf-8")
    _must(["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
           "-c", "copy", "-movflags", "+faststart", str(out)], "ghép clip")

def silence(seconds: float, out) -> None:
    """An audio track for a card with nothing to say.

    A transition card can carry no spoken line, and the voice service refuses text that
    is only punctuation with "No audio was received" — which used to end the whole render
    on sentence two. A silent track of the right length keeps the card in the film.
    """
    _must(["-y", "-v", "error", "-f", "lavfi", "-i",
           "anullsrc=channel_layout=stereo:sample_rate=24000",
           "-t", "%.3f" % max(0.8, float(seconds)), "-c:a", "libmp3lame", str(out)],
          "tao doan lang")
