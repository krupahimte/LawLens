"""Conversation memory in SQLite (Python standard library; no extra dependency).

History is used only to turn a follow-up ("what about the punishment?") into a standalone
question. It is deliberately NOT sent to the answering model, so earlier topics cannot
leak into the answer to the current question.
"""
import sqlite3
import time
import uuid

import config

DB_PATH = config.CONVERSATIONS_DB


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS messages ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL, "
        "role TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conv ON messages(conversation_id, id)")
    return conn


def new_conversation_id() -> str:
    return uuid.uuid4().hex


def add_message(conversation_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, time.time()),
        )


def get_history(conversation_id: str, limit: int = 6) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]
