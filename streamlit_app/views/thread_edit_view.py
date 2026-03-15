"""
views/thread_edit_view.py
Renders the "Edit Thread" panel.
Receives the thread_id to edit via st.session_state.show_edit_thread.
"""

import streamlit as st
from state import session
from services import api_client as services
from components.header import render_header
from utils.helpers import parse_tags


def render(thread_id: str) -> None:
    """Entry point — render the edit form for the given thread_id."""
    thread = _find_thread(thread_id)

    if not thread:
        st.error("Thread not found.")
        return

    render_header(title="✎ Edit Thread", subtitle="Update title or tags")

    new_title = st.text_input("Title", value=thread["title"], key="et_title")
    new_tags  = st.text_input(
        "Tags",
        value=", ".join(thread.get("tags") or []),
        key="et_tags",
    )

    col_save, col_cancel = st.columns([1, 3])

    with col_save:
        if st.button("Save →", type="primary", key="et_save"):
            _handle_save(thread_id, new_title, new_tags)

    with col_cancel:
        if st.button("Cancel", key="et_cancel"):
            session.go_to_chat()
            st.rerun()


# ── Private helpers ───────────────────────────────────────────────────────────

def _find_thread(thread_id: str) -> dict | None:
    return next(
        (t for t in session.get_threads() if t["_id"] == thread_id),
        None,
    )


def _handle_save(thread_id: str, new_title: str, new_tags_raw: str) -> None:
    tags     = parse_tags(new_tags_raw)
    data, ok = services.update_thread(thread_id, new_title.strip(), tags)

    if ok:
        # Refresh sidebar list
        threads_data, t_ok = services.fetch_threads()
        if t_ok:
            session.set_threads(threads_data)

        # If this thread is currently open in chat, refresh it too
        active = session.get_active_thread()
        if active and active["_id"] == thread_id:
            updated, th_ok = services.fetch_thread(thread_id)
            if th_ok:
                session.set_active_thread(updated)

        session.go_to_chat()
        st.rerun()
    else:
        st.error(data.get("error", "Update failed."))
