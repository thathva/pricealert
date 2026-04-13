import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent.parent / "data.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    phone       TEXT    NOT NULL,
    chat_id     TEXT    NOT NULL,
    asset       TEXT    NOT NULL,
    direction   TEXT    NOT NULL CHECK(direction IN ('above','below')),
    threshold   REAL    NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS message_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         TEXT    NOT NULL,
    phone           TEXT    NOT NULL,
    body            TEXT    NOT NULL,
    alert_id        INTEGER REFERENCES alerts(id),
    state           TEXT    NOT NULL DEFAULT 'queued'
                    CHECK(state IN ('queued','sending','delivered','failed','dead_letter')),
    retry_count     INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT,
    last_error      TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trigger_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id         INTEGER NOT NULL REFERENCES alerts(id),
    asset            TEXT    NOT NULL,
    direction        TEXT    NOT NULL,
    threshold        REAL    NOT NULL,
    price_at_trigger REAL    NOT NULL,
    phone            TEXT    NOT NULL,
    message_id       INTEGER REFERENCES message_queue(id),
    triggered_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    phone      TEXT PRIMARY KEY,
    chat_id    TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager: auto-commit on success, rollback on error."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(_SCHEMA)
