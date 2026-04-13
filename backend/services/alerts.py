"""Alert CRUD and trigger history."""
from __future__ import annotations

from database import db
from models import Alert, Direction, TriggerRecord


def create(phone: str, chat_id: str, asset: str, direction: Direction, threshold: float) -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO alerts (phone, chat_id, asset, direction, threshold) VALUES (?,?,?,?,?)",
            (phone, chat_id, asset.upper(), direction, threshold),
        )
        if cur.lastrowid is None:
            raise RuntimeError("INSERT did not return a row ID")
        return cur.lastrowid


def get_by_phone(phone: str) -> list[Alert]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE phone = ? AND active = 1 ORDER BY created_at DESC", (phone,)
        ).fetchall()
    return [Alert.model_validate(dict(r)) for r in rows]


def get_all_active() -> list[Alert]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM alerts WHERE active = 1").fetchall()
    return [Alert.model_validate(dict(r)) for r in rows]


def get_all(limit: int = 100) -> list[Alert]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [Alert.model_validate(dict(r)) for r in rows]


def get_by_id(alert_id: int) -> Alert | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    return Alert.model_validate(dict(row)) if row else None


def deactivate(alert_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE alerts SET active = 0 WHERE id = ?", (alert_id,))


def cancel_by_asset(asset: str, phone: str) -> int:
    with db() as conn:
        cur = conn.execute(
            "UPDATE alerts SET active = 0 WHERE asset = ? AND phone = ? AND active = 1",
            (asset.upper(), phone),
        )
        return cur.rowcount


def cancel_by_id(alert_id: int, phone: str) -> int:
    with db() as conn:
        cur = conn.execute(
            "UPDATE alerts SET active = 0 WHERE id = ? AND phone = ? AND active = 1",
            (alert_id, phone),
        )
        return cur.rowcount


def log_trigger(alert: Alert, price: float, message_id: int | None) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO trigger_history
               (alert_id, asset, direction, threshold, price_at_trigger, phone, message_id)
               VALUES (?,?,?,?,?,?,?)""",
            (alert.id, alert.asset, alert.direction, alert.threshold, price, alert.phone, message_id),
        )
        if cur.lastrowid is None:
            raise RuntimeError("INSERT did not return a row ID")
        return cur.lastrowid


def get_trigger_history(limit: int = 50) -> list[TriggerRecord]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM trigger_history ORDER BY triggered_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [TriggerRecord.model_validate(dict(r)) for r in rows]


def upsert_session(phone: str, chat_id: str) -> None:
    with db() as conn:
        conn.execute(
            """INSERT INTO chat_sessions (phone, chat_id, updated_at) VALUES (?,?,datetime('now'))
               ON CONFLICT(phone) DO UPDATE SET chat_id=excluded.chat_id, updated_at=excluded.updated_at""",
            (phone, chat_id),
        )
