"""
Lab1 - Secure REST API
======================
Endpoints:
  POST /auth/login   -> issue a JWT if username/password are correct
  GET  /api/data     -> protected, returns data list (requires Bearer JWT)
  POST /api/create   -> protected, creates a new record (requires Bearer JWT)

Security controls implemented:
  * SQL injection  : sqlite3 parameterized queries (?,?,?) - never string concat
  * XSS            : html.escape() on every user-controlled value before storage/output
  * AuthN          : JWT (HS256) verified on every protected route
  * Passwords      : bcrypt hashed at cost=12, never stored in plaintext
"""

import os
import html
import datetime
import sqlite3
import functools

import bcrypt
import jwt
from flask import Flask, request, jsonify, g

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_SECRET = os.environ.get("APP_SECRET", "change-me-in-production-please-32b")
JWT_ALGO = "HS256"
JWT_TTL_MIN = 30
DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = APP_SECRET


# ---------------------------------------------------------------------------
# Database helpers (parameterized queries only)
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and seed one demo user if missing."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            pw_hash BLOB NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    # Seed user: username=alice, password=CorrectHorse9!
    cur.execute("SELECT 1 FROM users WHERE username = ?", ("alice",))
    if cur.fetchone() is None:
        pw = b"CorrectHorse9!"
        pw_hash = bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))
        cur.execute(
            "INSERT INTO users (username, pw_hash) VALUES (?, ?)",
            ("alice", pw_hash),
        )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def make_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=JWT_TTL_MIN),
    }
    return jwt.encode(payload, APP_SECRET, algorithm=JWT_ALGO)


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "missing or malformed Authorization header"}), 401
        token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, APP_SECRET, algorithms=[JWT_ALGO])
            g.user = payload["sub"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid token"}), 401
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    # XSS defence: even at login, sanitize the incoming strings
    username = html.escape(str(data.get("username", "")).strip())
    password = str(data.get("password", "")).encode("utf-8")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    row = db.execute(
        "SELECT username, pw_hash FROM users WHERE username = ?", (username,)
    ).fetchone()

    # Always run bcrypt to mitigate user-enumeration timing attacks
    stored_hash = row["pw_hash"] if row else bcrypt.hashpw(b"dummy", bcrypt.gensalt(4))
    if not bcrypt.checkpw(password, stored_hash):
        return jsonify({"error": "invalid credentials"}), 401

    token = make_token(username)
    return jsonify({"access_token": token, "token_type": "Bearer", "expires_in": JWT_TTL_MIN * 60})


@app.route("/api/data", methods=["GET"])
@login_required
def get_data():
    db = get_db()
    rows = db.execute(
        "SELECT id, owner, content, created_at FROM items WHERE owner = ? ORDER BY id",
        (g.user,),
    ).fetchall()
    return jsonify(
        {
            "user": g.user,
            "items": [dict(r) for r in rows],
        }
    )


@app.route("/api/create", methods=["POST"])
@login_required
def create_item():
    data = request.get_json(silent=True) or {}
    raw_content = str(data.get("content", "")).strip()
    if not raw_content:
        return jsonify({"error": "content is required"}), 400

    # XSS defence: escape HTML metacharacters (< > & " ') before storage
    safe_content = html.escape(raw_content, quote=True)

    db = get_db()
    db.execute(
        "INSERT INTO items (owner, content, created_at) VALUES (?, ?, ?)",
        (g.user, safe_content, datetime.datetime.utcnow().isoformat()),
    )
    db.commit()
    return jsonify({"status": "created", "content": safe_content}), 201


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    # debug=False: never expose the interactive debugger in this lab
    app.run(host="127.0.0.1", port=5000, debug=False)
