"""WebSocket endpoint — one persistent connection per dashboard client."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services import broadcaster

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    q, initial = await broadcaster.subscribe()
    try:
        for msg in initial:
            await ws.send_text(msg)
        while True:
            msg = await q.get()
            await ws.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe(q)
        logger.debug("WebSocket client disconnected")
