"""LLM intent parsing - translates natural language SMS into structured alert actions."""
from __future__ import annotations

import logging
from typing import cast

import anthropic

from config import settings
from models import Alert, Direction, Prices
from services import alerts as alert_svc
from services import poller

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM = """\
You are a concise crypto price alert assistant accessed via iMessage/SMS.
Users set, check, and cancel price alerts for BTC, ETH, SOL, AVAX, BNB.
Keep replies SHORT - ideally under 160 characters. This is SMS.
Use tools to act. If intent is ambiguous, ask one short clarifying question.
"""

_TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "set_alert",
        "description": "Create a price alert. Call when user wants to be notified when price crosses a threshold.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset":     {"type": "string", "description": "BTC, ETH, SOL, AVAX, or BNB"},
                "direction": {"type": "string", "enum": ["above", "below"]},
                "threshold": {"type": "number", "description": "Price threshold in USD"},
            },
            "required": ["asset", "direction", "threshold"],
        },
    },
    {
        "name": "list_alerts",
        "description": "List all active alerts for this user.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cancel_alert",
        "description": "Cancel a price alert by asset name or alert ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset":    {"type": "string", "description": "Asset symbol e.g. BTC"},
                "alert_id": {"type": "integer", "description": "Specific alert ID if mentioned"},
            },
        },
    },
    {
        "name": "get_price",
        "description": "Get the current simulated price of one or more assets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of asset symbols e.g. ['BTC', 'ETH']. Omit to get all prices.",
                },
            },
        },
    },
]


def _format_alerts(active: list[Alert]) -> str:
    if not active:
        return "User has no active alerts."
    lines = ", ".join(f"#{a.id} {a.asset} {a.direction} ${a.threshold:,.2f}" for a in active)
    return f"User's active alerts: {lines}"


def _format_prices(prices: Prices) -> str:
    return "Current prices: " + ", ".join(f"{asset} ${price:,.2f}" for asset, price in prices.items())


def handle_message(message: str, phone: str, chat_id: str) -> str:
    """Parse user intent and execute the appropriate alert action. Returns SMS reply text."""
    context = f"{_format_alerts(alert_svc.get_by_phone(phone))}\n{_format_prices(poller.get_current_prices())}"

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=_SYSTEM,
        tools=_TOOLS,
        messages=[{"role": "user", "content": f"{context}\n\nMessage: {message}"}],
    )

    if response.stop_reason == "tool_use":
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        replies = [_dispatch(b.name, cast(dict[str, object], b.input), phone, chat_id) for b in tool_blocks]
        return "\n".join(replies)

    text_block = next((b for b in response.content if b.type == "text"), None)
    return text_block.text if text_block else "I didn't catch that. Try: 'alert me when BTC drops below 60k'"


def _dispatch(tool: str, inp: dict[str, object], phone: str, chat_id: str) -> str:
    if tool == "set_alert":
        try:
            asset = str(inp.get("asset", "")).upper()
            direction = str(inp.get("direction", "")).lower()
            threshold = float(inp.get("threshold", 0))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return "Sorry, I couldn't parse that. Try: 'alert me when BTC drops below 60k'"
        if asset not in ("BTC", "ETH", "SOL", "AVAX", "BNB"):
            return f"Unknown asset '{asset}'. Supported: BTC, ETH, SOL, AVAX, BNB."
        if direction not in ("above", "below"):
            return f"Direction must be 'above' or 'below'. Please clarify."
        if threshold <= 0:
            return "Threshold must be a positive number."
        alert_svc.create(phone=phone, chat_id=chat_id, asset=asset, direction=cast(Direction, direction), threshold=threshold)
        return f"Got it! I'll text you when {asset} goes {direction} ${threshold:,.0f}. Reply 'what am I tracking?' anytime."

    if tool == "list_alerts":
        active = alert_svc.get_by_phone(phone)
        if not active:
            return "No active alerts. Try: 'alert me when BTC drops below 60k'"
        lines = "\n".join(f"{i+1}. {a.asset} {a.direction} ${a.threshold:,.0f}" for i, a in enumerate(active))
        return f"Your alerts:\n{lines}\n\nReply 'cancel [asset]' to remove."

    if tool == "cancel_alert":
        asset = cast(str, inp.get("asset", ""))
        alert_id = cast(int | None, inp.get("alert_id"))
        changed = (
            alert_svc.cancel_by_id(alert_id=alert_id, phone=phone)
            if alert_id
            else alert_svc.cancel_by_asset(asset=asset, phone=phone)
        )
        return f"Cancelled your {asset} alert." if changed else "Couldn't find that alert. Reply 'what am I tracking?' to see active alerts."

    if tool == "get_price":
        prices = poller.get_current_prices()
        requested = [a.upper() for a in cast(list[str], inp.get("assets") or [])]
        subset = {k: v for k, v in prices.items() if k in requested} if requested else prices
        if not subset:
            return f"Unknown asset(s). Supported: {', '.join(prices)}"
        return " | ".join(f"{asset} ${price:,.2f}" for asset, price in subset.items())

    raise ValueError(f"Unknown tool: {tool}")
