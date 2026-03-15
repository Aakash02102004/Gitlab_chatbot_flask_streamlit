"""
views/auth_view.py
Renders the full-page authentication screen (login + register tabs).
Called by app.py when the user is not logged in.
"""

import streamlit as st
from state import session
from services import api_client as services


def render() -> None:
    """Render the centred auth card."""
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        _render_logo()
        tab_login, tab_register = st.tabs(["🔑  Login", "✨  Register"])

        with tab_login:
            _render_login_form()

        with tab_register:
            _render_register_form()


# ── Private helpers ───────────────────────────────────────────────────────────

def _render_logo() -> None:
    st.markdown(
        """
        <div style="text-align:center;margin-bottom:28px">
            <div style="font-size:2rem;font-weight:800;letter-spacing:-.02em">
                GitLab<span style="color:#e8622a">.</span>RAG
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:.78rem;
                        color:#555e80;margin-top:4px">
                // handbook intelligence engine
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_login_form() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    username = st.text_input("Username", key="li_user", placeholder="your_username")
    password = st.text_input("Password", key="li_pass", placeholder="••••••••", type="password")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Login →", type="primary", key="li_btn", use_container_width=True):
        if not username or not password:
            st.error("Please enter username and password.")
            return

        data, ok = services.login(username, password)
        if ok:
            # Seed threads and flip login flag
            threads_data, t_ok = services.fetch_threads()
            session.set_threads(threads_data if t_ok else [])
            st.session_state.logged_in = True
            st.session_state.username  = data.get("username", username)
            st.rerun()
        else:
            st.error(data.get("error", "Login failed."))


def _render_register_form() -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    r_user  = st.text_input("Username",         key="reg_user",  placeholder="pick_a_username")
    r_pass  = st.text_input("Password",         key="reg_pass",  placeholder="min 6 chars",    type="password")
    r_pass2 = st.text_input("Confirm password", key="reg_pass2", placeholder="repeat password", type="password")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Create account →", type="primary", key="reg_btn", use_container_width=True):
        if not r_user or not r_pass:
            st.error("All fields are required.")
        elif r_pass != r_pass2:
            st.error("Passwords do not match.")
        elif len(r_pass) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            data, ok = services.register(r_user, r_pass)
            if ok:
                st.success("Account created! Switch to the Login tab.")
            else:
                st.error(data.get("error", "Registration failed."))
