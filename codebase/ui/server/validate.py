"""The judge. Mechanical, no model opinion involved.

Same rules as fixtures/check.mjs, plus two the interface cannot check on its own: whether
the script actually reaches the length it was asked for, and whether every sentence that
asserts something cites a claim that is still alive.

Every function here returns a list of complaints written in Vietnamese, because the
complaints are fed straight back to the model as the revision brief. A complaint that
does not say what to do about it is wasted.
"""

from __future__ import annotations

import re

KIEU = {"ke", "giang", "nhe", "hoi", "nhan"}
SYLLABLES_PER_SECOND = 2.9
CHU_MAX = 40
DUR_TOLERANCE = 0.35          # per sentence, against words / 2.9
TOTAL_TOLERANCE = 0.15        # against the target the person asked for

# A word in shouting case with no lower-case letters, three or more long: an abbreviation
# the narrator would have to spell out loud.
SHOUTED = re.compile(r"\b[A-ZĐÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĨŨƠƯ]{3,}\b")

# A Vietnamese gloss in the same sentence satisfies the rule: the point is that the
# listener hears the meaning, not that the letters never appear. Without this, a lesson
# about HTTP caching could not name its own subject and the loop failed forever.
GLOSSED = re.compile(
    r"(giao thức|nghĩa là|hay còn gọi|gọi tắt|viết tắt|tức là|bộ nhớ đệm|tệp|máy chủ|"
    r"trình duyệt|ngôn ngữ|giao diện|dòng lệnh)",
    re.IGNORECASE,
)


def syllables(text: str) -> int:
    return len([w for w in re.split(r"\s+", (text or "").strip()) if w])


def expected_duration(loi: str) -> float:
    return syllables(loi) / SYLLABLES_PER_SECOND


def check_script(sentences: list[dict], sections: list[dict], claims: dict,
                 target_seconds: float, killed: dict | None = None) -> list[str]:
    killed = killed or {}
    out: list[str] = []
    if not sentences:
        return ["Kịch bản rỗng."]

    section_numbers = {s.get("no") for s in sections or []}
    introduced: set[str] = set()      # an abbreviation only needs explaining once

    for i, s in enumerate(sentences, start=1):
        n = s.get("n")
        loi = (s.get("loi") or "").strip()
        chu = (s.get("chu") or "").strip()
        tag = f"Câu {n}"

        if n != i:
            out.append(f"{tag}: số thứ tự phải liên tục từ một, câu này lẽ ra là {i}.")
        if not loi:
            out.append(f"{tag}: thiếu lời đọc.")
            continue

        if re.search(r"\d", loi):
            found = re.findall(r"\d+", loi)
            out.append(f"{tag}: lời đọc còn chữ số {', '.join(found)}. Viết thành chữ.")
        for word in SHOUTED.findall(loi):
            if word in introduced:
                continue                      # said once, explained once, that is enough
            introduced.add(word)
            if GLOSSED.search(loi):
                continue                      # the sentence explains it on the spot
            out.append(
                f"{tag}: '{word}' là viết tắt chưa giải thích. Nêu nghĩa tiếng Việt trước, "
                "ví dụ 'giao thức truyền siêu văn bản, gọi tắt là …'."
            )
        if re.search(r"\b\d{1,2}:\d{2}\b", loi):
            out.append(f"{tag}: không được có mã thời gian trong lời đọc.")
        if len(re.findall(r"[.!?]", loi)) > 1:
            out.append(f"{tag}: một câu một dòng, câu này chứa nhiều câu.")

        if s.get("kieu") not in KIEU:
            out.append(f"{tag}: kiểu đọc '{s.get('kieu')}' không hợp lệ, chọn một trong kể, giảng, thân mật, hỏi, chốt.")
        if not chu:
            out.append(f"{tag}: thiếu chữ trên màn hình.")
        elif len(chu) > CHU_MAX:
            out.append(f"{tag}: chữ trên màn hình dài {len(chu)} ký tự, tối đa bốn mươi.")
        elif chu.endswith(("…", "...")) or re.search(r"\w-$", chu):
            out.append(f"{tag}: chữ trên màn hình bị cắt giữa từ, viết lại cho gọn trong bốn mươi ký tự.")
        if not (s.get("hinh") or "").strip():
            out.append(f"{tag}: thiếu ý đồ hình.")

        if s.get("sec") not in section_numbers:
            out.append(f"{tag}: thuộc phần {s.get('sec')} nhưng phần đó không được khai báo.")

        cls = s.get("cls") or []
        if len(cls) != len(set(cls)):
            out.append(f"{tag}: cùng một mã dữ kiện được dẫn hai lần.")
        for cid in cls:
            if cid not in claims:
                out.append(f"{tag}: dẫn mã dữ kiện {cid} không tồn tại.")
            elif killed.get(cid):
                out.append(f"{tag}: dẫn dữ kiện {cid} đã bị người duyệt loại.")

        want = expected_duration(loi)
        have = float(s.get("dur") or 0)
        if want and abs(have - want) / want > DUR_TOLERANCE:
            out.append(f"{tag}: thời lượng {have} giây không khớp {syllables(loi)} âm tiết.")

    if target_seconds:
        total = sum(float(s.get("dur") or 0) for s in sentences)
        drift = (total - target_seconds) / target_seconds
        if abs(drift) > TOTAL_TOLERANCE:
            short = "thiếu" if drift < 0 else "dài"
            need = abs(target_seconds - total)
            out.append(
                f"Tổng thời lượng {round(total, 1)} giây, mục tiêu {round(target_seconds)} giây, "
                f"{short} khoảng {round(need)} giây. "
                + ("Viết thêm câu có dẫn nguồn, đừng kéo dài câu sẵn có."
                   if drift < 0 else "Bỏ hoặc gộp những câu ít thông tin nhất.")
            )
    return out


def uncited_assertions(sentences: list[dict]) -> list[str]:
    """A sentence with no claim is allowed only if it asserts nothing.

    We cannot judge meaning mechanically, so we flag the shape that is nearly always an
    assertion wearing a transition's clothes: a bare sentence with no claim that is long
    enough to be carrying a fact.
    """
    out: list[str] = []
    for s in sentences:
        if s.get("cls"):
            continue
        loi = (s.get("loi") or "").strip()
        if syllables(loi) >= 9:
            out.append(
                f"Câu {s.get('n')}: dài {syllables(loi)} âm tiết mà không dẫn dữ kiện nào. "
                "Nếu nó khẳng định điều gì thì phải có mã dữ kiện, nếu chỉ là câu chuyển thì viết ngắn lại."
            )
    return out


# A script does not narrate its own footnotes. Seen on a real run: "Sach ky thuat xac
# nhan rang viec nay giup tang hieu suat", pinned to a claim that said nothing of the
# kind. Vague authority in the voice-over is how padding disguises itself as evidence.
NARRATED_SOURCE = re.compile(
    r"(theo\s+(tài liệu|báo cáo|nghiên cứu|chuyên gia|số liệu)"
    r"|(sách|tài liệu|báo cáo|nghiên cứu|chuyên gia|giới chuyên môn)"
    r"(\s+\w+){0,2}\s+(xác nhận|khẳng định|chỉ ra|cho thấy|đánh giá|nhận định)"
    r"|được\s+(các\s+)?chuyên gia\s+(đánh giá|khẳng định))",
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


def overused_claims(sentences: list[dict], available: int) -> list[str]:
    """One claim carrying most of the script is a script leaning on one page.

    Seen on a real run: four consecutive sentences all citing t01, including one about
    containers that t01 did not support. The judge cannot read meaning, but it can see
    a claim being stretched.
    """
    if available < 4:
        return []
    counts: dict[str, int] = {}
    cited = 0
    for s in sentences:
        if not s.get("cls"):
            continue
        cited += 1
        for cid in s["cls"]:
            counts[cid] = counts.get(cid, 0) + 1
    if cited < 6:
        return []
    out = []
    for cid, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        if n / cited > 0.35:
            out.append(
                f"Dữ kiện {cid} đang đỡ {n} trên {cited} câu có dẫn nguồn. "
                f"Có {available} dữ kiện dùng được, hãy phân bổ ra thay vì dồn vào một cái."
            )
    return out


def claim_budget(target_seconds: float) -> int:
    """Roughly how many claims a script of this length needs to stay honest.

    One claim per two sentences, sentences averaging six seconds. Padding a long video
    from a handful of claims is how a script starts asserting things nobody checked.
    """
    sentences = max(1, round(target_seconds / 6.0))
    return max(3, round(sentences / 2))
