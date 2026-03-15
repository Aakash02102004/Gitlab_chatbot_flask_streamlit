"""
services/api_client.py
All HTTP communication with the Flask backend.

Every public function returns a (data: dict | list, ok: bool) tuple.
The caller decides how to surface errors; this layer only raises on
network-level failures (caught and returned as error dicts).
"""

import os
from dotenv import load_dotenv
from state.session import get_http_session

load_dotenv()

_BASE = os.environ.get("FLASK_BASE_URL", "http://localhost:5000").rstrip("/")


# ── Internal transport ────────────────────────────────────────────────────────

def _call(method: str, path: str, **kwargs) -> tuple[dict | list, bool]:
    """
    Execute an HTTP request against the Flask API.
    Returns (response_data, success_bool).
    """
    http = get_http_session()
    url  = _BASE + "/api" + path
    try:
        response = getattr(http, method)(url, timeout=120, **kwargs)
        data     = response.json()
        ok       = response.status_code < 400
        return data, ok
    except Exception as exc:
        return {"error": str(exc)}, False


# ── Auth ──────────────────────────────────────────────────────────────────────

def login(username: str, password: str) -> tuple[dict, bool]:
    return _call("post", "/auth/login", json={"username": username, "password": password})


def register(username: str, password: str) -> tuple[dict, bool]:
    return _call("post", "/auth/register", json={"username": username, "password": password})


def logout() -> tuple[dict, bool]:
    return _call("post", "/auth/logout")


def get_me() -> tuple[dict, bool]:
    return _call("get", "/auth/me")


# ── Threads ───────────────────────────────────────────────────────────────────

def fetch_threads() -> tuple[list, bool]:
    return _call("get", "/threads")


def fetch_thread(thread_id: str) -> tuple[dict, bool]:
    return _call("get", f"/threads/{thread_id}")


def create_thread(title: str, tags: list[str]) -> tuple[dict, bool]:
    return _call("post", "/threads", json={"title": title, "tags": tags})


def update_thread(thread_id: str, title: str, tags: list[str]) -> tuple[dict, bool]:
    return _call("put", f"/threads/{thread_id}", json={"title": title, "tags": tags})


def delete_thread(thread_id: str) -> tuple[dict, bool]:
    return _call("delete", f"/threads/{thread_id}")


# ── Queries ───────────────────────────────────────────────────────────────────

def create_query(thread_id: str, question: str) -> tuple[dict, bool]:
    return _call("post", f"/threads/{thread_id}/queries", json={"question": question})
