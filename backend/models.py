"""Shared data models used across services and routers."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

MessageState = Literal["queued", "sending", "delivered", "failed", "dead_letter"]
Direction = Literal["above", "below"]
Asset = Literal["BTC", "ETH", "SOL", "AVAX", "BNB"]
Prices = dict[str, float]  # asset -> USD price


class Alert(BaseModel):
    id: int
    phone: str
    chat_id: str
    asset: Asset
    direction: Direction
    threshold: float
    active: bool
    created_at: str


class QueueMessage(BaseModel):
    id: int
    chat_id: str
    phone: str
    body: str
    alert_id: int | None
    state: MessageState
    retry_count: int
    next_attempt_at: str | None
    last_error: str | None
    created_at: str
    updated_at: str


class TriggerRecord(BaseModel):
    id: int
    alert_id: int
    asset: Asset
    direction: Direction
    threshold: float
    price_at_trigger: float
    phone: str
    message_id: int | None
    triggered_at: str
