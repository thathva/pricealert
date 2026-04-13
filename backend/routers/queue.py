from __future__ import annotations

from fastapi import APIRouter

from models import QueueMessage
from services import message_queue

router = APIRouter(prefix="/api")


@router.get("/queue")
def get_queue() -> list[QueueMessage]:
    return message_queue.get_all()
