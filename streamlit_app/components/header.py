"""
components/header.py
Renders the top header bar for each main panel.
"""

import streamlit as st


def render_header(title: str, subtitle: str = "", title_color: str = "#e8e8f0") -> None:
    """
    Emit a styled page-header block.

    Args:
        title:       Primary heading text.
        subtitle:    Secondary mono-font line (optional).
        title_color: CSS colour for the title (default white-ish).
    """
    sub_html = (
        f'<div class="page-header-sub">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="page-header">
            <div style="flex:1;min-width:0">
                <div class="page-header-title" style="color:{title_color}">{title}</div>
                {sub_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
