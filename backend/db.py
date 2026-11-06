"""SQLite helpers: users, login tokens, history."""
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("HC_DATA_DIR", BASE / "data"))
UPLOADS = DATA_DIR / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
TOKEN_DAYS = 30        # stay logged in for 30 days


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def init():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                pw_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tokens(
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                check_type TEXT NOT NULL,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                status TEXT NOT NULL,
                probs TEXT NOT NULL,
                quality TEXT NOT NULL,
                has_heatmap INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_hist_user ON history(user_id, created);
            """
        )


def hash_pw(password: str, salt: str | None = None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return h.hex(), salt


def check_pw(password: str, pw_hash: str, salt: str) -> bool:
    h, _ = hash_pw(password, salt)
    return hmac.compare_digest(h, pw_hash)


def new_token(user_id: int) -> str:
    t = secrets.token_urlsafe(32)
    with conn() as c:
        c.execute("INSERT INTO tokens(token,user_id,created) VALUES(?,?,?)", (t, user_id, time.time()))
    return t


def user_for_token(token: str):
    if not token:
        return None
    with conn() as c:
        r = c.execute(
            "SELECT u.* FROM tokens t JOIN users u ON u.id=t.user_id WHERE t.token=? AND t.created>?",
            (token, time.time() - TOKEN_DAYS * 86400),
        ).fetchone()
    return dict(r) if r else None


def delete_token(token: str):
    with conn() as c:
        c.execute("DELETE FROM tokens WHERE token=?", (token,))


def remove_files_for(history_id: int):
    for suffix in ("_img.jpg", "_heat.png"):
        p = UPLOADS / f"{history_id}{suffix}"
        if p.exists():
            p.unlink()
