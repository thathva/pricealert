"""Linq API client - narrow interface, all HTTP details stay here."""
from __future__ import annotations

import hashlib
import hmac

import httpx

from config import settings

_BASE = "https://api.linqapp.com/api/partner/v3"

_http = httpx.Client(
    base_url=_BASE,
    headers={"Authorization": f"Bearer {settings.linq_api_key}"},
)


def close() -> None:
    _http.close()


def send_message(chat_id: str, text: str) -> None:
    payload = {"message": {"parts": [{"type": "text", "value": text}]}}
    _http.post(f"/chats/{chat_id}/messages", json=payload).raise_for_status()



def verify_webhook_signature(raw_body: bytes, timestamp: str, signature: str) -> bool:
    secret = settings.linq_webhook_secret
    if not secret:
        raise ValueError("LINQ_WEBHOOK_SECRET is not configured")
    message = f"{timestamp}.{raw_body.decode()}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
