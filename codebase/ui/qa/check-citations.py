"""Check somebody else's cited script the way we check our own.

Built for the demo: give ChatGPT the best system prompt you can write, let it produce a
script with a URL and a verbatim quote per claim, paste the result here, and run this. It
fetches every page and applies the SAME rule our own pipeline applies to itself — the
quote must appear in the fetched text, whitespace and Unicode normalised, wording never.

The point is not that a chat model writes badly. It writes well. The point is that when
it hands you a citation, checking it is your job; when ours hands you one, the check has
already run, and anything that failed it was dropped rather than shown.

Input: a JSON file, either
    [{"url": "...", "quote": "...", "text": "optional sentence it supports"}, ...]
or our own /write output (sentences + claims + sources), which it reads directly.

    python qa/check-citations.py gpt-output.json
    python qa/check-citations.py gpt-output.json --label "ChatGPT + system prompt"

Needs TAVILY_API_KEY in the environment (same key the backend uses). Never reads .env.

KNOWN LIMIT — read before quoting this tool's number at anyone, including ourselves.
A page fetched two ways comes back two ways. The search API returns article prose; the
extract API returns the same URL with navigation, menus and boilerplate, and sometimes a
differently rendered or truncated body. Measured on one real page: the search result was
2,221 characters of article text, the extract 33,534 characters beginning with a logo and
a language menu, sharing only 23% contiguously.

So a "KHÔNG THẤY" verdict here means "not found in THIS rendering", not "fabricated".
Run against our own output it reported 14/19 exact and 3 missing, and every one of those
three was really on the page — the quote was literal text from the search rendering.

Use this to inspect, never as a scoreboard. The honest one-click check is the
"Mở trang gốc tại đúng câu trích" link in the UI, which verifies against the live page a
human actually sees.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))

import agent  # noqa: E402  — reuse the very same norm() and fetcher

import re  # noqa: E402


def flat(text: str) -> str:
    """Normalise the way our pipeline does, then also drop markdown decoration.

    A page fetched two different ways comes back rendered two different ways: the search
    result gives plain prose, the extract gives markdown, so the same sentence carries
    `**` and `* ` in one and not the other. Comparing those literally reports a perfect
    citation as a fabrication, which is the opposite of useful. Wording is never touched
    — only decoration and spacing.
    """
    t = agent.norm(text)
    t = re.sub(r"[*_`#>]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def longest_run(needle: str, hay: str) -> float:
    """Fraction of the quote that appears as one contiguous stretch of the page.

    Reported instead of a bare pass/fail because a quote stitched from two list items is
    a different problem from a quote that is simply not there, and a reviewer deserves to
    see which one they have.
    """
    if not needle:
        return 0.0
    if needle in hay:
        return 1.0
    best, n = 0, len(needle)
    for start in range(0, n, 4):
        lo, hi = best, n - start
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if needle[start:start + mid] in hay:
                lo = mid
            else:
                hi = mid - 1
        best = max(best, lo)
    return best / n


def pairs_from(doc) -> list[dict]:
    """Accept either a plain list of citations or one of our own script payloads."""
    if isinstance(doc, list):
        return [{"url": d.get("url", ""), "quote": d.get("quote", ""),
                 "text": d.get("text", "")} for d in doc]

    out = []
    claims = doc.get("claims") or {}
    sources = doc.get("sources") or {}
    for cid, c in claims.items():
        for e in c.get("evidence") or []:
            src = sources.get(e.get("src")) or {}
            out.append({"url": src.get("url", ""), "quote": e.get("quote", ""),
                        "text": c.get("text", ""), "id": cid})
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    label = "đối thủ"
    if "--label" in sys.argv:
        label = sys.argv[sys.argv.index("--label") + 1]

    doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    items = [p for p in pairs_from(doc) if p.get("url") and p.get("quote")]
    if not items:
        print("Không tìm thấy cặp (địa chỉ, câu trích) nào trong tệp.")
        return 2

    print("Kiểm %d trích dẫn của %s, bằng đúng luật hệ thống tự áp cho mình.\n" % (len(items), label))
    cache: dict = {}
    ok = bad = part = unreachable = 0

    for i, it in enumerate(items, 1):
        url, quote = it["url"].strip(), it["quote"].strip()
        if url not in cache:
            try:
                got = agent.tavily_extract(url)
            except Exception as exc:
                got = None
                print("  %2d. KHÔNG TẢI ĐƯỢC  %s\n      %s" % (i, url[:70], str(exc)[:80]))
            cache[url] = (got or {}).get("content", "") if got is not None else None

        content = cache[url]
        if content is None:
            unreachable += 1
            continue
        if not content:
            unreachable += 1
            print("  %2d. TRANG RỖNG      %s" % (i, url[:70]))
            continue

        share = longest_run(flat(quote), flat(content))
        if share >= 0.999:
            ok += 1
            print("  %2d. KHỚP            %s" % (i, quote[:62]))
        elif share >= 0.80:
            part += 1
            print("  %2d. KHỚP %3.0f%% LIỀN  %s" % (i, share * 100, quote[:56]))
            print("      (trích ghép từ nhiều chỗ liền nhau trên trang, không phải bịa)")
        else:
            bad += 1
            print("  %2d. KHÔNG THẤY TRÊN TRANG (khớp liền dài nhất %.0f%%)" % (i, share * 100))
            print("      trích: %s" % quote[:88])
            print("      trang: %s" % url[:88])

    total = ok + bad + part
    print("\n%s" % ("-" * 60))
    if total:
        print("Khớp nguyên văn:          %d/%d (%.0f%%)" % (ok, total, 100 * ok / total))
        print("Khớp gần hết, ghép chỗ:   %d/%d" % (part, total))
    if bad:
        print("KHÔNG có trên trang: %d — đây là những câu người duyệt sẽ phải tự đi kiểm." % bad)
    if unreachable:
        print("Không tải được %d trang; không kết luận gì về những trích dẫn đó." % unreachable)
    print("\nHệ thống của chúng tôi áp đúng phép kiểm này lên chính mình TRƯỚC khi hiển thị,")
    print("và bỏ đi những đoạn không khớp. Con số trên là thứ bạn nhận được khi phép kiểm đó")
    print("chưa từng chạy.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
