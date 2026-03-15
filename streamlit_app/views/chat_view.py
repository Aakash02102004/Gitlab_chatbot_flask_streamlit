"""
views/chat_view.py
Renders the main chat panel for the active thread.
Shows message history and the query input form.
"""

import streamlit as st
from state import session
from services import api_client as services
from components.chat_bubble import render_user_bubble, render_ai_bubble
from components.header import render_header
from utils.helpers import fmt_date


def render() -> None:
    """Entry point — renders either the empty-state or the active thread chat."""
    thread = session.get_active_thread()

    if not thread:
        _render_no_thread()
        return

    _render_thread_header(thread)
    _render_message_history(thread)
    st.markdown("<hr>", unsafe_allow_html=True)
    _render_query_form(thread)


# ── Private helpers ───────────────────────────────────────────────────────────

def _render_no_thread() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">◈</div>
            <div class="title">No thread selected</div>
            <div class="hint">
                Pick an existing thread from the sidebar,<br>
                or create a new one to get started.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_thread_header(thread: dict) -> None:
    tags_html = "".join(
        f'<span class="tag-pill">{tag}</span>'
        for tag in (thread.get("tags") or [])
    )
    subtitle = fmt_date(thread.get("updated_at", ""))
    if tags_html:
        subtitle += f"&nbsp;&nbsp;{tags_html}"

    render_header(title=thread["title"], subtitle=subtitle)


def _render_message_history(thread: dict) -> None:
    queries = thread.get("queries") or []

    if not queries:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">◎</div>
                <div class="title">Thread is empty</div>
                <div class="hint">
                    Ask your first question below.<br>
                    The RAG engine will search the GitLab handbook and reply with sources.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for query in queries:
        render_user_bubble(query["question"])
        render_ai_bubble(
            answer=query["answer"],
            sources=query.get("sources") or [],
            created_at=query.get("created_at", ""),
        )


def _render_query_form(thread: dict) -> None:
    with st.form(key="query_form", clear_on_submit=True):
        question = st.text_area(
            "",
            placeholder="Ask anything about the GitLab handbook…  (Enter to send)",
            height=90,
            label_visibility="collapsed",
            key="query_input",
        )
        col_send, col_hint = st.columns([1, 5])
        with col_send:
            submitted = st.form_submit_button(
                "Send ↑", type="primary", use_container_width=True
            )
        with col_hint:
            st.markdown(
                "<div style='padding-top:8px;font-family:JetBrains Mono,monospace;"
                "font-size:.75rem;color:#404560'>"
                "RAG will retrieve the most relevant handbook sections before answering."
                "</div>",
                unsafe_allow_html=True,
            )

    if submitted:
        _handle_submit(thread, question)


def _handle_submit(thread: dict, question: str) -> None:
    if not question.strip():
        st.warning("Please enter a question.")
        return

    with st.spinner("🔍 Searching handbook…"):
        data, ok = services.create_query(thread["_id"], question.strip())

    if ok:
        # Reload the full thread so the new query appears in history
        updated, t_ok = services.fetch_thread(thread["_id"])
        if t_ok:
            session.set_active_thread(updated)
        st.rerun()
    else:
        st.error(data.get("error", "Query failed. Is the Flask server running?"))
