from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from codebase.script_agent import (  # noqa: E402
    FixtureSearchProvider,
    GeminiProvider,
    LessonBrief,
    TavilySearchProvider,
    generate_script,
    research_with_langgraph,
    save_run_log,
)

st.set_page_config(page_title="ScriptScout CP3", page_icon="🎬", layout="wide")
st.title("ScriptScout — CP3 prototype")
st.caption("AI tìm nguồn và viết bản nháp kịch bản; human duyệt nguồn trước khi sinh nội dung.")

with st.form("brief"):
    topic = st.text_input("Chủ đề", value="Prompt engineering cơ bản")
    learning_goal = st.text_area(
        "Mục tiêu bài học",
        value="Người học giải thích được prompt và viết được một prompt đơn giản.",
    )
    learner = st.text_input("Người học là ai", value="Sinh viên mới học AI")
    duration = st.number_input("Thời lượng video (phút)", min_value=0.5, max_value=120.0, value=2.0)
    use_fixture = st.checkbox(
        "Dùng fixture để demo/eval tái lập (bỏ chọn để dùng Tavily + Gemini thật)",
        value=not bool(os.getenv("TAVILY_API_KEY")),
    )
    submitted = st.form_submit_button("1. Tìm nguồn")

if submitted:
    brief = LessonBrief(topic, learning_goal, learner, duration)
    try:
        provider = FixtureSearchProvider() if use_fixture else TavilySearchProvider()
        st.session_state["brief"] = brief
        st.session_state["sources"] = research_with_langgraph(brief, provider)
        st.session_state.pop("result", None)
    except Exception as exc:
        st.error(str(exc))

sources = st.session_state.get("sources", [])
brief = st.session_state.get("brief")
if sources and brief:
    st.subheader("Human Gate 1 — duyệt nguồn")
    st.write("Chỉ các nguồn được chọn mới được đưa vào prompt viết kịch bản.")
    approved_ids: list[str] = []
    for source in sources:
        suspicious = f" ⚠️ {source.warning}" if source.warning else ""
        with st.expander(f"{source.id} · {source.title} · trust {source.trust_score:.0%}{suspicious}"):
            st.write(source.snippet)
            st.caption(f"{source.publisher} · {source.published_at} · {source.url}")
            st.write("Lý do:", "; ".join(source.trust_reasons))
            if st.checkbox("Duyệt nguồn này", value=source.trust_score >= 0.65 and not source.warning, key=source.id):
                approved_ids.append(source.id)

    if st.button("2. Viết kịch bản từ nguồn đã duyệt"):
        approved = [source for source in sources if source.id in approved_ids]
        try:
            ai_provider = None if use_fixture else GeminiProvider()
            result = generate_script(brief, approved, provider=ai_provider)
            st.session_state["result"] = result
            save_run_log(result, ROOT / "logs" / "latest_run.json")
        except Exception as exc:
            st.error(str(exc))

result = st.session_state.get("result")
if result:
    st.subheader("Human Gate 2 — duyệt kịch bản")
    for sentence in result.sentences:
        with st.container(border=True):
            st.markdown(f"**Câu {sentence.number}**")
            st.write(sentence.speech)
            st.caption(f"Màn hình: {sentence.on_screen}")
            st.caption(f"Ý đồ hình: {sentence.visual_intent}")
            st.write("Nguồn:", ", ".join(sentence.source_ids) or "Câu dẫn, không cần nguồn")
    for warning in result.warnings:
        st.warning(warning)
    st.download_button(
        "Tải JSON kết quả",
        data=__import__("json").dumps(
            {
                "brief": result.brief.__dict__,
                "sources": [source.__dict__ for source in result.sources],
                "sentences": [sentence.__dict__ for sentence in result.sentences],
            },
            ensure_ascii=False,
            indent=2,
        ),
        file_name="scriptscout-draft.json",
        mime="application/json",
    )
