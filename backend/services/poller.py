"""Price simulation and alert threshold evaluation."""
from __future__ import annotations

import logging
import math
import random
import threading

from models import Prices
from services import alerts as alert_svc
from services import broadcaster, message_queue

logger = logging.getLogger(__name__)

_BASE_PRICES: dict[str, float] = {
    "BTC":  65_000,
    "ETH":   3_200,
    "SOL":     180,
    "AVAX":     35,
    "BNB":     580,
}

_tick: int = 0
_last_prices: Prices = dict(_BASE_PRICES)
_overrides: dict[str, float] = {}  # asset -> manually set price
_lock = threading.Lock()


def _simulate(tick: int) -> Prices:
    """Sine wave ±5% around base prices, with small random noise."""
    t = tick * 0.08
    return {
        asset: round(base * (1 + 0.05 * math.sin(t) + random.uniform(-0.002, 0.002)), 2)
        for asset, base in _BASE_PRICES.items()
    }


def _publish(prices: Prices) -> None:
    """Evaluate alert thresholds and broadcast new prices. Called after releasing the lock."""
    fired = False
    for alert in alert_svc.get_all_active():
        price = prices.get(alert.asset)
        if price is None:
            continue
        if (alert.direction == "above" and price >= alert.threshold) or \
           (alert.direction == "below" and price <= alert.threshold):
            alert_svc.deactivate(alert.id)
            body = (
                f"Alert fired: {alert.asset} is ${price:,.2f} - "
                f"{alert.direction} your ${alert.threshold:,.0f} threshold."
            )
            msg_id = message_queue.enqueue(chat_id=alert.chat_id, phone=alert.phone, body=body, alert_id=alert.id)
            alert_svc.log_trigger(alert=alert, price=price, message_id=msg_id)
            logger.info("alert %d triggered: %s @ $%.2f", alert.id, alert.asset, price)
            fired = True

    if fired:
        broadcaster.broadcast("alerts", alert_svc.get_all())
        broadcaster.broadcast("history", alert_svc.get_trigger_history())

    broadcaster.broadcast("prices", prices)


def get_current_prices() -> Prices:
    with _lock:
        return dict(_last_prices)


def tick() -> Prices:
    """Advance simulation one step. Returns new prices."""
    global _tick, _last_prices
    with _lock:
        _tick += 1
        prices = _simulate(_tick)
        prices.update(_overrides)
        _last_prices = prices
    _publish(prices)
    return prices


def set_price_override(asset: str, price: float) -> Prices:
    """Manually set an asset price and immediately evaluate thresholds."""
    global _last_prices
    with _lock:
        _overrides[asset.upper()] = price
        prices = _simulate(_tick)
        prices.update(_overrides)
        _last_prices = prices
    _publish(prices)
    return prices
