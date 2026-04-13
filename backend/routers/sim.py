"""Price endpoints — current prices and simulation overrides."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services import poller

router = APIRouter(prefix="/api")


class PriceOverrideBody(BaseModel):
    asset: str
    price: float


@router.get("/prices")
def get_prices() -> dict:
    return poller.get_current_prices()


@router.post("/sim/prices")
def override_price(body: PriceOverrideBody) -> dict:
    prices = poller.set_price_override(body.asset, body.price)
    return {"prices": prices}
