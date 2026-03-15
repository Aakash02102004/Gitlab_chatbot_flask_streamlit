"""
views/thread_delete_view.py
Renders the delete-confirmation panel for a thread.
Receives the thread_id to delete via st.session_state.confirm_delete.
"""

import streamlit as st
from state import session
from services import api_client as services
from components.header import render_header


def render(thread_id: str) -> None:
    """Entry point — render the confirmation screen for the given thread_id."""
    thread = _find_thread(thread_id)
    title  = thread["title"] if thread else thread_id

    render_header(
        title="⚠ Delete Thread",
        subtitle="This action cannot be undone",
        title_color="#e05050",
    )

    st.warning(
        f'Are you sure you want to delete **"{title}"**? '
        "All queries inside will be permanently removed."
    )

    col_del, col_cancel = st.columns([1, 3])

    with col_del:
        if st.button("🗑  Delete permanently", key="cd_confirm"):
            _handle_delete(thread_id)

    with col_cancel:
        if st.button("Cancel", key="cd_cancel"):
            session.go_to_chat()
            st.rerun()


# ── Private helpers ───────────────────────────────────────────────────────────

def _find_thread(thread_id: str) -> dict | None:
    return next(
        (t for t in session.get_threads() if t["_id"] == thread_id),
        None,
    )


def _handle_delete(thread_id: str) -> None:
    data, ok = services.delete_thread(thread_id)

    if ok:
        # Clear active thread if it was the one deleted
        active = session.get_active_thread()
        if active and active["_id"] == thread_id:
            session.set_active_thread(None)

        # Refresh sidebar list
        threads_data, t_ok = services.fetch_threads()
        if t_ok:
            session.set_threads(threads_data)

        session.go_to_chat()
        st.rerun()
    else:
        st.error(data.get("error", "Delete failed."))
