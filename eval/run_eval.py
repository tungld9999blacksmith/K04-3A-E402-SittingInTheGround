from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from codebase.script_agent import FixtureSearchProvider, LessonBrief, generate_script, research_with_langgraph  # noqa: E402
from codebase.metrics import citation_coverage, summarize_case_results  # noqa: E402


def main() -> None:
    cases = json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))
    results: list[dict] = []
    for case in cases:
        brief = LessonBrief(**case["input"])
        sources = research_with_langgraph(brief, FixtureSearchProvider())
        approved = [source for source in sources if not source.warning and source.trust_score >= 0.65]
        try:
            result = generate_script(brief, approved)
            sentences = [sentence.__dict__ for sentence in result.sentences]
            passed = bool(sentences) and citation_coverage(sentences) >= 0.8
            results.append({"id": case["id"], "category": case["category"], "passed": passed, "note": ""})
        except Exception as exc:
            results.append({"id": case["id"], "category": case["category"], "passed": False, "note": str(exc)})
    summary = summarize_case_results(results)
    lines = [
        "# CP3 evaluation — first run",
        "",
        f"- Total: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Pass rate: {summary['pass_rate']:.1%}",
        "",
        "| ID | Category | Passed | Note |",
        "|---|---|---:|---|",
    ]
    lines.extend(f"| {item['id']} | {item['category']} | {item['passed']} | {item['note']} |" for item in results)
    lines += [
        "",
        "## Interpretation",
        "",
        "Eval mode dùng fixture để tái lập; demo mode có thể dùng Tavily/Gemini thật.",
        "Các case cần human chấm citation correctness và source reliability trước khi chốt quality bar.",
    ]
    (ROOT / "eval" / "run_results.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
