import io

# ---- the judge learns to catch narrated sourcing and a stretched claim sooner ----
p = "server/validate.py"
s = io.open(p, encoding="utf-8").read()

old = '''def overused_claims(sentences: list[dict], available: int) -> list[str]:'''
new = '''# A script does not narrate its own footnotes. Seen on a real run: "Sach ky thuat xac
# nhan rang viec nay giup tang hieu suat", pinned to a claim that said nothing of the
# kind. Vague authority in the voice-over is how padding disguises itself as evidence.
NARRATED_SOURCE = re.compile(
    r"(theo\\s+(tài liệu|báo cáo|nghiên cứu|chuyên gia|số liệu)"
    r"|(sách|tài liệu|báo cáo|nghiên cứu|chuyên gia|giới chuyên môn)\\s+"
    r"(kỹ thuật\\s+)?(xác nhận|khẳng định|chỉ ra|cho thấy|đánh giá|nhận định)"
    r"|được\\s+(các\\s+)?chuyên gia\\s+(đánh giá|khẳng định))",
    re.IGNORECASE,
)


def narrated_sourcing(sentences: list[dict]) -> list[str]:
    """The provenance belongs in the ledger, not in the narration."""
    out: list[str] = []
    for s in sentences:
        m = NARRATED_SOURCE.search(s.get("loi") or "")
        if m:
            out.append(
                f"Câu {s.get('n')}: lời đọc tự kể nguồn ('{m.group(0)}'). "
                "Nói thẳng nội dung, phần dẫn nguồn đã nằm ở hồ sơ nguồn rồi."
            )
    return out


def overused_claims(sentences: list[dict], available: int) -> list[str]:'''
assert old in s, "overused anchor"
s = s.replace(old, new, 1)

old = '''        if n / cited > 0.4:'''
new = '''        if n / cited > 0.35:'''
assert old in s, "threshold"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("judge: narrated sourcing, tighter spread")

# ---- wire it in, both places the whole script is judged ----
p = "server/agent.py"
s = io.open(p, encoding="utf-8").read()
n = s.count("+ validate.overused_claims(sentences, len(usable)))")
assert n == 2, "expected two judge calls, found %d" % n
s = s.replace("+ validate.overused_claims(sentences, len(usable)))",
              "+ validate.overused_claims(sentences, len(usable))\n"
              "                + validate.narrated_sourcing(sentences))")
# and in the rewrite path
old = '''    problems = validate.check_script(kept, sections, claims, target, dead) + \\
        validate.uncited_assertions(kept)
    if problems:'''
new = '''    problems = (validate.check_script(kept, sections, claims, target, dead)
                + validate.uncited_assertions(kept)
                + validate.narrated_sourcing(kept))
    if problems:'''
assert old in s, "rewrite judge"
s = s.replace(old, new, 1)

# tell the writer up front, so the first draft is already clean
old = '''    "- Không lặp lại tên chủ đề hai lần trong cùng một câu."'''
new = '''    "- Không lặp lại tên chủ đề hai lần trong cùng một câu.\\n"
    "- KHÔNG tự kể nguồn trong lời đọc. Không viết 'theo tài liệu', 'sách kỹ thuật xác "
    "nhận', 'báo cáo chỉ ra', 'chuyên gia đánh giá'. Nói thẳng nội dung; phần dẫn nguồn "
    "nằm ở cls.\\n"
    "- Không viết câu chung chung để cho đủ thời lượng. Mỗi câu phải nói một điều cụ thể "
    "lấy từ dữ kiện.\\n"
    "- Phân bổ đều các dữ kiện, đừng dồn nhiều câu vào một dữ kiện."'''
assert old in s, "rules tail"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("writer told up front; rewrite judged too")
