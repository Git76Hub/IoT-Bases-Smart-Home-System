"""SQLite message log used for charts and auditing."""
import sqlite3
import time

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    ts      REAL NOT NULL,
    topic   TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_topic_ts ON messages (topic, ts);
"""


def connect() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def log_message(conn: sqlite3.Connection, topic: str, payload: str, ts: float | None = None) -> None:
    conn.execute(
        "INSERT INTO messages (ts, topic, payload) VALUES (?, ?, ?)",
        (ts if ts is not None else time.time(), topic, payload),
    )
    conn.commit()


def prune(conn: sqlite3.Connection, days: int = 7) -> None:
    conn.execute("DELETE FROM messages WHERE ts < ?", (time.time() - days * 86400,))
    conn.commit()


def history(conn: sqlite3.Connection, topic: str, since: float, max_points: int = 300):
    """Numeric history as [(timestamp, value), ...], thinned to max_points."""
    rows = conn.execute(
        "SELECT ts, CAST(payload AS REAL) FROM messages WHERE topic = ? AND ts >= ? ORDER BY ts",
        (topic, since),
    ).fetchall()
    if len(rows) > max_points:
        step = len(rows) / max_points
        rows = [rows[int(i * step)] for i in range(max_points)]
    return rows
