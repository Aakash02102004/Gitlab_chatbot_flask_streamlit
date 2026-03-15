"""
components/chat_bubble.py
Renders individual chat message bubbles (user question + AI answer).
"""

import streamlit as st
from utils.helpers import fmt_date, trim_url


def render_user_bubble(question: str) -> None:
    """Render the right-aligned user question bubble."""
    st.markdown(
        f"""
        <div class="bubble-label">You</div>
        <div class="bubble-user">{question}</div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_bubble(answer: str, sources: list[str], created_at: str = "") -> None:
    """
    Render the left-aligned AI answer bubble with optional source chips
    and a timestamp footer.

    Args:
        answer:     Plain-text (or HTML-safe) answer from the RAG engine.
        sources:    List of source URLs to display as clickable chips.
        created_at: ISO-8601 timestamp string for the footer.
    """
    sources_html = _build_sources_html(sources)
    timestamp_html = (
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.68rem;'
        f'color:#353850;text-align:right;margin-bottom:16px">{fmt_date(created_at)}</div>'
        if created_at else ""
    )

    st.markdown(
        f"""
        <div class="bubble-label">GitLab Expert</div>
        <div class="bubble-ai">
            {answer}
            {sources_html}
        </div>
        {timestamp_html}
        """,
        unsafe_allow_html=True,
    )


def _build_sources_html(sources: list[str]) -> str:
    """Return the sources section HTML, or an empty string if no sources."""
    if not sources:
        return ""
    chips = "".join(
        f'<a class="source-chip" href="{s}" target="_blank">{trim_url(s)}</a>'
        for s in sources
    )
    return (
        '<div class="sources-row">'
        '<div class="bubble-label" style="margin-bottom:4px">Sources</div>'
        f"{chips}"
        "</div>"
    )
