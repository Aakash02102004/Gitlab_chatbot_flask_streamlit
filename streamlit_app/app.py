"""
app.py  –  GitLab Handbook RAG  •  Streamlit UI
================================================
Entry point for the Streamlit application.

Run:
    streamlit run app.py

The Flask backend (main.py) must be running at FLASK_BASE_URL
(default: http://localhost:5000).
"""

import streamlit as st

# ── Page config must be the FIRST Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="GitLab Handbook RAG",
    page_icon="🦊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Internal imports (after set_page_config) ──────────────────────────────────
from styles.css import APP_CSS
from state import session
from components.sidebar import render_sidebar
from views.auth_view import render as render_auth
from views.chat_view import render as render_chat
from views.thread_create_view import render as render_thread_create
from views.thread_edit_view import render as render_thread_edit
from views.thread_delete_view import render as render_thread_delete

# ── One-time setup ────────────────────────────────────────────────────────────
st.markdown(APP_CSS, unsafe_allow_html=True)
session.init()


# ── Router ────────────────────────────────────────────────────────────────────
def main() -> None:
    # Not logged in → show auth screen, nothing else
    if not session.is_logged_in():
        render_auth()
        return

    # Logged in → sidebar is always visible
    render_sidebar()

    # Main panel routing based on navigation flags
    if st.session_state.show_new_thread:
        render_thread_create()

    elif st.session_state.show_edit_thread:
        render_thread_edit(st.session_state.show_edit_thread)

    elif st.session_state.confirm_delete:
        render_thread_delete(st.session_state.confirm_delete)

    else:
        render_chat()


if __name__ == "__main__":
    main()
