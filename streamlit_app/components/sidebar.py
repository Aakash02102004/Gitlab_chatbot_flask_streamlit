"""
components/sidebar.py
Renders the left sidebar: branding, new-thread button, search,
thread list with open/edit/delete actions, and logout.
"""

from requests import session as requests_session
import streamlit as st
import services
from state import session
from utils.helpers import fmt_date


def render_sidebar() -> None:
    """Entry point — call once per render cycle from app.py."""
    with st.sidebar:
        _render_brand()
        _render_new_thread_btn()
        st.markdown("<hr>", unsafe_allow_html=True)
        search = _render_search()
        _render_thread_list(search)
        st.markdown("<hr>", unsafe_allow_html=True)
        _render_logout()


# ── Private helpers ───────────────────────────────────────────────────────────

def _render_brand() -> None:
    st.markdown(
        f"""
        <div style="padding:10px 4px 16px">
            <div style="font-size:1.1rem;font-weight:800;letter-spacing:-.02em">
                GL<span style="color:#e8622a">.</span>RAG
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:.7rem;
                        color:#555e80;margin-top:2px">
                logged in as
                <span style="color:#e8622a">{session.get_username()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_new_thread_btn() -> None:
    if st.button("＋ New Thread", key="sb_new_btn"):
        session.show_new_thread()
        st.rerun()


def _render_search() -> str:
    return st.text_input(
        "",
        placeholder="🔍  Search threads…",
        key="sb_search",
        label_visibility="collapsed",
    )


def _render_thread_list(search: str) -> None:
    threads = session.get_threads()
    if search:
        threads = [t for t in threads if search.lower() in t["title"].lower()]

    if not threads:
        st.markdown(
            """
            <div style="text-align:center;padding:24px 8px;color:#3a4060;
                        font-size:.8rem;font-family:'JetBrains Mono',monospace">
                No threads yet.<br>Create one above ↑
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    active_id = (session.get_active_thread() or {}).get("_id")

    for thread in threads:
        _render_thread_card(thread, is_active=(thread["_id"] == active_id))


def _render_thread_card(thread: dict, is_active: bool) -> None:
    tid        = thread["_id"]
    card_class = "thread-card active" if is_active else "thread-card"
    tags_html  = "".join(
        f'<span class="tag-pill">{tag}</span>'
        for tag in (thread.get("tags") or [])
    )

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="thread-card-title" title="{thread['title']}">{thread['title']}</div>
            <div class="thread-card-meta">{fmt_date(thread.get('updated_at', ''))}</div>
            {('<div style="margin-top:5px">' + tags_html + "</div>") if tags_html else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_open, col_edit, col_del = st.columns([3, 1, 1])

    with col_open:
        if st.button("Open", key=f"open_{tid}", use_container_width=True):
            data, ok = services.api_client.fetch_thread(tid)
            if ok:
                session.set_active_thread(data)
                session.go_to_chat()
                st.rerun()
            else:
                st.error(data.get("error", "Could not load thread."))

    with col_edit:
        if st.button("✎", key=f"edit_{tid}", use_container_width=True):
            session.show_edit_thread(tid)
            st.rerun()

    with col_del:
        if st.button("✕", key=f"del_{tid}", use_container_width=True):
            session.show_delete_confirm(tid)
            st.rerun()


def _render_logout() -> None:
    if st.button("⏻  Logout", key="sb_logout", use_container_width=True):
        services.api_client.logout()
        session.reset()
        st.rerun()
