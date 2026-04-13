"""Message queue — enqueue outbound messages and manage their state machine."""
from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta, timezone

from database import db
from models import MessageState, QueueMessage

_lock = threading.Lock()
_loop: asyncio.AbstractEventLoop | None = None
_work_event: asyncio.Event | None = None

_BACKOFF_SECONDS = [5, 15, 45]
MAX_RETRIES = len(_BACKOFF_SECONDS)


def init(loop: asyncio.AbstractEventLoop, event: asyncio.Event) -> None:
    global _loop, _work_event
    _loop = loop
    _work_event = event


def backoff_for(completed_attempts: int) -> int:
    return _BACKOFF_SECONDS[min(completed_attempts - 1, len(_BACKOFF_SECONDS) - 1)]


def next_attempt_iso(completed_attempts: int) -> str:
    delay = backoff_for(completed_attempts)
    return (datetime.now(timezone.utc) + timedelta(seconds=delay)).strftime("%Y-%m-%d %H:%M:%S")


def enqueue(chat_id: str, phone: str, body: str, alert_id: int | None = None) -> int:
    with _lock, db() as conn:
        cur = conn.execute(
            "INSERT INTO message_queue (chat_id, phone, body, alert_id) VALUES (?,?,?,?)",
            (chat_id, phone, body, alert_id),
        )
        if cur.lastrowid is None:
            raise RuntimeError("INSERT did not return a row ID")
        row_id = cur.lastrowid
    if _loop and _work_event:
        _loop.call_soon_threadsafe(_work_event.set)
    return row_id


def get_queued(limit: int = 5) -> list[QueueMessage]:
    with db() as conn:
        rows = conn.execute(
            """SELECT * FROM message_queue
               WHERE state = 'queued'
                 AND (next_attempt_at IS NULL OR next_attempt_at <= datetime('now'))
               ORDER BY created_at ASC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [QueueMessage.model_validate(dict(r)) for r in rows]


def set_state(
    msg_id: int,
    state: MessageState,
    error: str | None = None,
    retry_count: int | None = None,
    next_attempt_at: str | None = None,
) -> None:
    with _lock, db() as conn:
        conn.execute(
            """UPDATE message_queue
               SET state           = ?,
                   last_error      = COALESCE(?, last_error),
                   retry_count     = COALESCE(?, retry_count),
                   next_attempt_at = COALESCE(?, next_attempt_at),
                   updated_at      = datetime('now')
               WHERE id = ?""",
            (state, error, retry_count, next_attempt_at, msg_id),
        )


def get_all(limit: int = 100) -> list[QueueMessage]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM message_queue ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [QueueMessage.model_validate(dict(r)) for r in rows]
