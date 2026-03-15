"""
utils/helpers.py
Pure utility functions with no Streamlit or app-state dependencies.
"""

from datetime import datetime


def fmt_date(iso: str) -> str:
    """Convert an ISO-8601 datetime string to a compact human-readable form."""
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%-d %b, %H:%M")
    except Exception:
        return iso[:16]


def trim_url(url: str, max_len: int = 55) -> str:
    """Truncate a URL to max_len characters, appending ellipsis if needed."""
    return url if len(url) <= max_len else url[:max_len] + "…"


def parse_tags(raw: str) -> list[str]:
    """Split a comma-separated tag string into a cleaned list."""
    return [t.strip() for t in raw.split(",") if t.strip()]
