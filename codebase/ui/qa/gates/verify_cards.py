"""Gate for server/cards.py. Written by the reviewer, not the worker."""
import sys, os
sys.path.insert(0, "server")
sys.stdout.reconfigure(encoding="utf-8")

import cards
from PIL import Image

W, H = 1920, 1080
OUT = "verify-out"
os.makedirs(OUT, exist_ok=True)

LONG_VI = ("Hệ thống tên miền dịch tên trang thành địa chỉ máy để trình duyệt biết "
           "phải hỏi máy chủ nào trước khi tải nội dung về")

cases = [
    dict(name="plain", eyebrow="BỘ NHỚ ĐỆM", title="Lần thứ hai nhanh hơn",
         caption="Nhờ đó dữ liệu được lấy ngay tại chỗ.", footer_left="Nguồn: MDN, web.dev",
         footer_right="2 / 8"),
    dict(name="long", eyebrow="HỆ THỐNG TÊN MIỀN", title="Tên miền thành địa chỉ máy",
         caption=LONG_VI, footer_left="Nguồn: Stanford", footer_right="3 / 8"),
    dict(name="notitlecap", eyebrow=None, title="DNS cho người mới", caption="",
         footer_left="", footer_right=""),
    dict(name="withbg", eyebrow="MỤC MỘT", title="Có ảnh nền", caption="Chữ vẫn phải đọc được.",
         footer_left="Nguồn: Wikimedia", footer_right="1 / 8", bg=True),
]

bg = Image.new("RGB", (W, H), (120, 140, 160))
for x in range(0, W, 40):                       # a busy background: text must survive it
    for y in range(0, H, 40):
        if (x // 40 + y // 40) % 2 == 0:
            bg.paste((230, 230, 230), (x, y, min(x + 40, W), min(y + 40, H)))

fails = []
for c in cases:
    kwargs = dict(c)
    name = kwargs.pop("name")
    if kwargs.pop("bg", False):
        kwargs["bg"] = bg
    img = cards.card(**kwargs)
    if not isinstance(img, Image.Image):
        fails.append(f"{name}: card() must return a PIL Image, got {type(img)}")
        continue
    if img.size != (W, H):
        fails.append(f"{name}: size {img.size}, expected {(W, H)}")
    path = os.path.join(OUT, name + ".png")
    img.save(path)

    # Nothing may be painted in the outer 40px margin: that is where text runs off screen.
    px = img.load()
    edge_ink = 0
    for x in range(0, W, 7):
        for y in (8, 20, H - 20, H - 8):
            r, g, b = px[x, y][:3]
            if r > 200 and g > 200 and b > 200:
                edge_ink += 1
    if edge_ink > 40:
        fails.append(f"{name}: bright pixels in the top/bottom margin ({edge_ink}); text is overflowing")

    if img.convert("L").resize((1, 1)).getpixel((0, 0)) > 200:
        fails.append(f"{name}: the card is almost white; the ground should be dark")

if fails:
    print("FAIL")
    for f in fails:
        print(" -", f)
    sys.exit(1)

print("OK: 4 cards rendered at 1920x1080, nothing in the margins")
