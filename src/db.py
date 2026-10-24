import json
import sqlite3
from datetime import datetime

from .config import DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY, sender TEXT, subject TEXT, date TEXT, snippet TEXT,
                spam_prob REAL, label TEXT, flags TEXT, links TEXT,
                processed_at TEXT, feedback TEXT)"""
        )


def seen_ids():
    with _conn() as c:
        return {r["id"] for r in c.execute("SELECT id FROM emails")}


def save(parsed: dict, result: dict):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO emails VALUES (?,?,?,?,?,?,?,?,?,?,NULL)",
            (parsed["id"], parsed["sender"], parsed["subject"], parsed["date"], parsed["snippet"],
             result["spam_prob"], result["label"], json.dumps(parsed["flags"]),
             json.dumps(parsed["links"][:20]), datetime.now().isoformat(timespec="seconds")),
        )


def recent(limit=200):
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM emails ORDER BY processed_at DESC LIMIT ?", (limit,))]


def set_feedback(email_id: str, feedback: str):
    """feedback: 'wrong' or 'correct'. Used later to build a retraining set."""
    with _conn() as c:
        c.execute("UPDATE emails SET feedback=? WHERE id=?", (feedback, email_id))
