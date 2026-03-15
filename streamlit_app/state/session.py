"""
state/session.py
Single source of truth for st.session_state keys.

- init()         : call once at app startup to set all defaults.
- Typed getters  : convenience wrappers so the rest of the app never
                   touches raw string keys directly.
"""

import streamlit as st


# ── Default values ────────────────────────────────────────────────────────────

_DEFAULTS: dict = {
    "logged_in":        False,
    "username":         "",
    "session_cookie":   None,   # holds a persistent requests.Session object
    "threads":          [],
    "active_thread":    None,   # full thread dict including its queries list
    "show_new_thread":  False,
    "show_edit_thread": False,  # False  OR  the thread_id being edited
    "confirm_delete":   None,   # None   OR  the thread_id pending deletion
}


def init() -> None:
    """Initialise any missing session-state keys with their defaults."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset() -> None:
    """Wipe all app keys (used on logout)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init()


# ── Typed convenience accessors ───────────────────────────────────────────────

def is_logged_in() -> bool:
    return bool(st.session_state.get("logged_in", False))


def get_username() -> str:
    return st.session_state.get("username", "")


def get_threads() -> list:
    return st.session_state.get("threads", [])


def set_threads(threads: list) -> None:
    st.session_state.threads = threads


def get_active_thread() -> dict | None:
    return st.session_state.get("active_thread")


def set_active_thread(thread: dict | None) -> None:
    st.session_state.active_thread = thread


def get_http_session():
    """Return (and lazily create) the persistent requests.Session."""
    import requests
    if st.session_state.session_cookie is None:
        st.session_state.session_cookie = requests.Session()
    return st.session_state.session_cookie


# ── Navigation flags ──────────────────────────────────────────────────────────

def show_new_thread() -> None:
    st.session_state.show_new_thread  = True
    st.session_state.show_edit_thread = False
    st.session_state.confirm_delete   = None


def show_edit_thread(thread_id: str) -> None:
    st.session_state.show_edit_thread = thread_id
    st.session_state.show_new_thread  = False
    st.session_state.confirm_delete   = None


def show_delete_confirm(thread_id: str) -> None:
    st.session_state.confirm_delete   = thread_id
    st.session_state.show_new_thread  = False
    st.session_state.show_edit_thread = False


def go_to_chat() -> None:
    """Clear all panel flags to return to the normal chat view."""
    st.session_state.show_new_thread  = False
    st.session_state.show_edit_thread = False
    st.session_state.confirm_delete   = None
