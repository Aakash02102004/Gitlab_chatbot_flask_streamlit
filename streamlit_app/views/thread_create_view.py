"""
views/thread_create_view.py
Renders the "New Thread" creation panel.
"""

import streamlit as st
from state import session
from services import api_client as services
from components.header import render_header
from utils.helpers import parse_tags


def render() -> None:
    """Entry point — render the new-thread form."""
    render_header(
        title="＋ New Thread",
        subtitle="Create a conversation thread in the handbook",
    )

    title    = st.text_input("Thread title", placeholder="e.g. GitLab core values", key="nt_title")
    tags_raw = st.text_input(
        "Tags (comma-separated, optional)",
        placeholder="culture, remote, values",
        key="nt_tags",
    )

    col_create, col_cancel = st.columns([1, 3])

    with col_create:
        if st.button("Create →", type="primary", key="nt_create"):
            _handle_create(title, tags_raw)

    with col_cancel:
        if st.button("Cancel", key="nt_cancel"):
            session.go_to_chat()
            st.rerun()


# ── Private helpers ───────────────────────────────────────────────────────────

def _handle_create(title: str, tags_raw: str) -> None:
    if not title.strip():
        st.error("Please enter a title.")
        return

    tags      = parse_tags(tags_raw)
    data, ok  = services.create_thread(title.strip(), tags)

    if ok:
        # Refresh the sidebar thread list and open the new thread
        threads_data, t_ok = services.fetch_threads()
        if t_ok:
            session.set_threads(threads_data)

        thread_data, th_ok = services.fetch_thread(data["_id"])
        if th_ok:
            session.set_active_thread(thread_data)

        session.go_to_chat()
        st.rerun()
    else:
        st.error(data.get("error", "Failed to create thread."))
