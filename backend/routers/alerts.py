from __future__ import annotations

from fastapi import APIRouter

from models import Alert, TriggerRecord
from services import alerts as alert_svc

router = APIRouter(prefix="/api")


@router.get("/alerts")
def list_alerts() -> list[Alert]:
    return alert_svc.get_all()


@router.get("/alerts/history")
def trigger_history() -> list[TriggerRecord]:
    return alert_svc.get_trigger_history()
