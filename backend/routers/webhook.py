"""Inbound webhook from Linq - receives messages, parses intent, enqueues reply."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError

from services import alerts as alert_svc
from services import broadcaster, linq_client, llm, message_queue

logger = logging.getLogger(__name__)
router = APIRouter()


class _Part(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: str
    value: str = ""

class _MessageData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    chat: dict[str, object]
    parts: list[_Part] = []
    sender_handle: dict[str, object]
    direction: str

class _Payload(BaseModel):
    data: _MessageData


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_webhook_event: str = Header(default=""),
    x_webhook_timestamp: str = Header(default=""),
    x_webhook_signature: str = Header(default=""),
) -> dict:
    raw_body = await request.body()

    if not linq_client.verify_webhook_signature(raw_body, x_webhook_timestamp, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if x_webhook_event != "message.received":
        return {"ok": True}

    try:
        payload = _Payload.model_validate_json(raw_body)
    except ValidationError:
        return {"ok": True}

    data = payload.data
    text_part = next((p for p in data.parts if p.type == "text"), None)

    if data.direction != "inbound" or not text_part:
        return {"ok": True}

    phone = str(data.sender_handle["handle"])
    chat_id = str(data.chat["id"])

    alert_svc.upsert_session(phone, chat_id)

    try:
        reply = llm.handle_message(message=text_part.value, phone=phone, chat_id=chat_id)
    except Exception as exc:
        logger.exception("LLM error for %s: %s", phone, exc)
        reply = "Sorry, something went wrong on my end. Try again!"

    message_queue.enqueue(chat_id=chat_id, phone=phone, body=reply)

    broadcaster.broadcast("alerts", alert_svc.get_all())
    broadcaster.broadcast("queue", message_queue.get_all())

    return {"ok": True}
