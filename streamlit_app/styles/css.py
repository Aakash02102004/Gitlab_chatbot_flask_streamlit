"""
styles/css.py
All application CSS in a single constant. Injected once at startup via app.py.
"""

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #111318;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: #c8cad8;
    font-size: 0.85rem;
    padding: 0.45rem 0.75rem;
    transition: all 0.15s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1c2030;
    border-color: #2a3050;
    color: #fff;
}

/* ── chat bubbles ── */
.bubble-user {
    background: #1a2540;
    border: 1px solid #2a3a6a;
    border-radius: 14px 14px 4px 14px;
    padding: 12px 16px;
    margin: 6px 0 6px 15%;
    font-size: 0.9rem;
    line-height: 1.6;
    color: #e0e4f0;
}
.bubble-ai {
    background: #161a24;
    border: 1px solid #1e2535;
    border-radius: 4px 14px 14px 14px;
    padding: 14px 18px;
    margin: 6px 15% 6px 0;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #d8dce8;
}
.bubble-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #555e80;
    margin-bottom: 4px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.source-chip {
    display: inline-block;
    background: #1a1208;
    border: 1px solid #3a2a08;
    border-radius: 4px;
    padding: 2px 9px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #c89030;
    margin: 3px 4px 3px 0;
    text-decoration: none;
    word-break: break-all;
}
.source-chip:hover { opacity: 0.75; }
.sources-row { margin-top: 10px; }

/* ── thread card in sidebar ── */
.thread-card {
    background: #161920;
    border: 1px solid #1e2535;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: border-color 0.15s;
}
.thread-card:hover { border-color: #e8622a55; }
.thread-card.active { border-color: #e8622a; background: #1c1f2c; }
.thread-card-title {
    font-weight: 600; font-size: 0.88rem; color: #dde0ee;
    margin-bottom: 2px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.thread-card-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: #555e80;
}

/* ── page header ── */
.page-header {
    display: flex; align-items: center; gap: 12px;
    padding-bottom: 14px; border-bottom: 1px solid #1e2535; margin-bottom: 20px;
}
.page-header-title { font-size: 1.25rem; font-weight: 700; color: #e8e8f0; }
.page-header-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: #555e80; margin-top: 2px;
}
.accent { color: #e8622a; }

/* ── empty state ── */
.empty-state { text-align: center; color: #404560; padding: 60px 20px; }
.empty-state .icon  { font-size: 3rem; margin-bottom: 12px; }
.empty-state .title { font-size: 1rem; font-weight: 600; margin-bottom: 6px; color: #555e80; }
.empty-state .hint  { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; line-height: 1.6; }

/* ── input area ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #161a24 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 10px !important;
    color: #dde0ee !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #e8622a !important;
    box-shadow: 0 0 0 1px #e8622a33 !important;
}

/* ── primary button ── */
.stButton > button[kind="primary"] {
    background: #e8622a !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #fff !important;
    transition: opacity 0.15s !important;
}
.stButton > button[kind="primary"]:hover { opacity: 0.88 !important; }

/* ── danger button ── */
.btn-danger > button {
    background: #8b1a1a !important;
    border: none !important;
    border-radius: 8px !important;
    color: #fff !important;
}

/* ── tag pills ── */
.tag-pill {
    display: inline-block;
    background: #1c2030;
    border: 1px solid #2a3050;
    border-radius: 20px;
    padding: 2px 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #6878a8;
    margin-right: 5px;
}

/* ── divider ── */
hr { border-color: #1e2535 !important; margin: 16px 0 !important; }

/* ── alert boxes ── */
[data-testid="stAlert"] { border-radius: 10px !important; }
</style>
"""
