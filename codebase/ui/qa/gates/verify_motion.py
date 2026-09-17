"""Gate for server/motion.py. Written by the reviewer, not the worker."""
import sys, os, subprocess
sys.path.insert(0, "server")
sys.stdout.reconfigure(encoding="utf-8")

import motion
from PIL import Image
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = "verify-out"
os.makedirs(OUT, exist_ok=True)


def probe(path):
    p = subprocess.run([FF, "-i", path], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.stderr


def seconds(path):
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", probe(path))
    assert m, "no duration in ffmpeg output for " + path
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


fails = []

# a still and two audio tracks of known, different lengths
img = os.path.join(OUT, "still.png")
Image.new("RGB", (1920, 1080), (12, 40, 80)).save(img)
for name, secs in (("a.mp3", 3.0), ("b.mp3", 5.0)):
    subprocess.run([FF, "-y", "-v", "error", "-f", "lavfi",
                    "-i", "anullsrc=channel_layout=stereo:sample_rate=24000",
                    "-t", str(secs), os.path.join(OUT, name)], check=True)

a, b = os.path.join(OUT, "a.mp3"), os.path.join(OUT, "b.mp3")

got = motion.duration_of(a)
if abs(got - 3.0) > 0.25:
    fails.append(f"duration_of said {got}, the file is 3.0s")

c1, c2 = os.path.join(OUT, "c1.mp4"), os.path.join(OUT, "c2.mp4")
motion.ken_burns(img, a, c1, zoom_in=True)
motion.ken_burns(img, b, c2, zoom_in=False)

for path, want in ((c1, 3.0), (c2, 5.0)):
    if not os.path.exists(path):
        fails.append(f"{path} was not produced")
        continue
    d = seconds(path)
    if abs(d - want) > 0.3:
        fails.append(f"{os.path.basename(path)} is {d}s, the narration is {want}s")
    info = probe(path)
    if "1920x1080" not in info:
        fails.append(f"{os.path.basename(path)} is not 1920x1080")
    if "Audio:" not in info:
        fails.append(f"{os.path.basename(path)} has no audio track")

# The picture must actually move: two frames far apart cannot be identical.
if os.path.exists(c2):
    for t, tag in ((0.2, "early"), (4.4, "late")):
        subprocess.run([FF, "-y", "-v", "error", "-ss", str(t), "-i", c2, "-frames:v", "1",
                        os.path.join(OUT, f"f_{tag}.png")], check=True)
    f1 = Image.open(os.path.join(OUT, "f_early.png")).convert("L").resize((64, 36))
    f2 = Image.open(os.path.join(OUT, "f_late.png")).convert("L").resize((64, 36))
    diff = sum(abs(x - y) for x, y in zip(f1.getdata(), f2.getdata())) / (64 * 36)
    if diff < 0.4:
        fails.append(f"frames at 0.2s and 4.4s are nearly identical (mean diff {diff:.2f}); "
                     "there is no camera movement")

joined = os.path.join(OUT, "joined.mp4")
motion.concat([c1, c2], joined)
if not os.path.exists(joined):
    fails.append("concat produced nothing")
else:
    d = seconds(joined)
    if abs(d - 8.0) > 0.5:
        fails.append(f"joined clip is {d}s, expected about 8.0s")

if fails:
    print("FAIL")
    for f in fails:
        print(" -", f)
    sys.exit(1)

print("OK: clips match their narration length, are 1920x1080, carry audio, move, and join")
