import os
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Import RAG components from rag.py
from rag_chain import ask_handbook

load_dotenv()

# ─────────────────────────────────────────────
# App & DB setup
# ─────────────────────────────────────────────

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")
CORS(app, supports_credentials=True)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.environ.get("DB_NAME", "gitlab_rag")

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

users_col   = db["users"]
threads_col = db["threads"]
queries_col = db["queries"]

# Unique index: one username per user
users_col.create_index("username", unique=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def serialize(doc):
    """Convert MongoDB document to JSON-serialisable dict."""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


def now_utc():
    return datetime.now(timezone.utc)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Unauthorised – please log in"}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated


def owns_thread(thread_id: str) -> dict | None:
    """Return thread doc if it belongs to the current user, else None."""
    try:
        oid = ObjectId(thread_id)
    except Exception:
        return None
    return threads_col.find_one({"_id": oid, "user_id": g.user_id})


# ─────────────────────────────────────────────
# Auth routes
# ─────────────────────────────────────────────

@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    try:
        result = users_col.insert_one({
            "username":      username,
            "password_hash": generate_password_hash(password),
            "created_at":    now_utc(),
        })
    except Exception:
        return jsonify({"error": "username already taken"}), 409

    return jsonify({"message": "Registered successfully", "user_id": str(result.inserted_id)}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = users_col.find_one({"username": username})
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session.permanent = True
    session["user_id"] = str(user["_id"])
    return jsonify({"message": "Logged in", "username": username})


@app.post("/api/auth/logout")
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.get("/api/auth/me")
@login_required
def me():
    user = users_col.find_one({"_id": ObjectId(g.user_id)}, {"password_hash": 0})
    return jsonify(serialize(user))


# ─────────────────────────────────────────────
# Thread CRUD  (/api/threads)
# ─────────────────────────────────────────────

@app.get("/api/threads")
@login_required
def list_threads():
    """List all threads for the logged-in user (newest first)."""
    docs = list(threads_col.find(
        {"user_id": g.user_id},
        sort=[("updated_at", -1)]
    ))
    return jsonify([serialize(d) for d in docs])


@app.post("/api/threads")
@login_required
def create_thread():
    """Create a new thread."""
    data  = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip() or "New thread"
    tags  = data.get("tags", [])

    result = threads_col.insert_one({
        "user_id":    g.user_id,
        "title":      title,
        "tags":       tags,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    })
    doc = threads_col.find_one({"_id": result.inserted_id})
    return jsonify(serialize(doc)), 201


@app.get("/api/threads/<thread_id>")
@login_required
def get_thread(thread_id):
    """Get a single thread with all its queries."""
    thread = owns_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    queries = list(queries_col.find(
        {"thread_id": thread_id},
        sort=[("created_at", 1)]
    ))
    thread = serialize(thread)
    thread["queries"] = [serialize(q) for q in queries]
    return jsonify(thread)


@app.put("/api/threads/<thread_id>")
@login_required
def update_thread(thread_id):
    """Update thread metadata (title, tags)."""
    thread = owns_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    data   = request.get_json(silent=True) or {}
    update = {"updated_at": now_utc()}
    if "title" in data:
        update["title"] = (data["title"] or "").strip() or "Untitled"
    if "tags" in data:
        update["tags"] = data["tags"]

    threads_col.update_one({"_id": thread["_id"]}, {"$set": update})
    doc = threads_col.find_one({"_id": thread["_id"]})
    return jsonify(serialize(doc))


@app.delete("/api/threads/<thread_id>")
@login_required
def delete_thread(thread_id):
    """Delete a thread and all its queries."""
    thread = owns_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    queries_col.delete_many({"thread_id": thread_id})
    threads_col.delete_one({"_id": thread["_id"]})
    return jsonify({"message": "Thread deleted"})


# ─────────────────────────────────────────────
# Query routes  (/api/threads/<id>/queries)
# ─────────────────────────────────────────────

@app.get("/api/threads/<thread_id>/queries")
@login_required
def list_queries(thread_id):
    """List all queries in a thread."""
    if not owns_thread(thread_id):
        return jsonify({"error": "Thread not found"}), 404

    docs = list(queries_col.find(
        {"thread_id": thread_id},
        sort=[("created_at", 1)]
    ))
    return jsonify([serialize(d) for d in docs])


@app.post("/api/threads/<thread_id>/queries")
@login_required
def create_query(thread_id):
    """
    Create a new query inside a thread.
    Calls ask_handbook() and stores both the question and the RAG answer.
    """
    thread = owns_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    # ── Call RAG ──
    try:
        rag_result = ask_handbook(question)
        answer     = rag_result.get("answer", "")
        sources    = rag_result.get("sources", [])
    except Exception as e:
        return jsonify({"error": f"RAG error: {str(e)}"}), 500

    # ── Persist query ──
    query_doc = {
        "thread_id":  thread_id,
        "user_id":    g.user_id,
        "question":   question,
        "answer":     answer,
        "sources":    sources,
        "created_at": now_utc(),
    }
    result = queries_col.insert_one(query_doc)

    # Update thread's updated_at timestamp
    threads_col.update_one(
        {"_id": thread["_id"]},
        {"$set": {"updated_at": now_utc()}}
    )

    doc = queries_col.find_one({"_id": result.inserted_id})
    return jsonify(serialize(doc)), 201


# ─────────────────────────────────────────────
# Serve SPA (optional – for the bundled UI)
# ─────────────────────────────────────────────

@app.get("/")
def index():
    return app.send_static_file("index.html")


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
