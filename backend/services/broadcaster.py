"""WebSocket broadcaster - single hub for pushing real-time state to dashboard clients.

Services call broadcast() after any mutation. The WebSocket endpoint subscribes and
streams events to connected browsers. Thread-safe: background threads use
loop.call_soon_threadsafe so asyncio queues are never touched cross-thread.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from pydantic import TypeAdapter

from services import alerts as alert_svc
from services import message_queue as mq
from services import poller

logger = logging.getLogger(__name__)

_adapter = TypeAdapter(Any)
_subscribers: set[asyncio.Queue[str]] = set()
_loop: asyncio.AbstractEventLoop | None = None


def set_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


def _fmt(event: str, data: object) -> str:
    return _adapter.dump_json({"event": event, "data": data}).decode()


def _deliver(msg: str) -> None:
    """Enqueue a message for every subscriber. Must run on the event loop."""
    for q in set(_subscribers):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            logger.warning("slow WebSocket client - event dropped")


def broadcast(event: str, data: object) -> None:
    """Thread-safe: schedule delivery on the event loop from any thread."""
    if _loop is None or _loop.is_closed():
        return
    _loop.call_soon_threadsafe(_deliver, _fmt(event, data))


def snapshot() -> list[str]:
    """Full current state sent to each new subscriber on connect."""
    return [
        _fmt("alerts",  alert_svc.get_all()),
        _fmt("queue",   mq.get_all()),
        _fmt("prices",  poller.get_current_prices()),
        _fmt("history", alert_svc.get_trigger_history()),
    ]


async def subscribe() -> tuple[asyncio.Queue[str], list[str]]:
    """Register a new WebSocket client. Returns its queue and the initial snapshot."""
    initial = snapshot()
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
    _subscribers.add(q)
    return q, initial


def unsubscribe(q: asyncio.Queue[str]) -> None:
    _subscribers.discard(q)
