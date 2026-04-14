"""Queue processor - drains queued messages and retries on failure."""
from __future__ import annotations

import logging

import httpx

from models import QueueMessage
from services import broadcaster, linq_client, message_queue

logger = logging.getLogger(__name__)


def _send(msg: QueueMessage) -> None:
    message_queue.set_state(msg.id, "sending")
    try:
        linq_client.send_message(msg.chat_id, msg.body)
        message_queue.set_state(msg.id, "delivered")
        logger.info("delivered msg %d to %s", msg.id, msg.phone)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("msg %d HTTP %d - %s", msg.id, status, exc)
        # Non-retryable: bad request, auth failure, not found
        if status in (400, 401, 403, 404):
            message_queue.set_state(msg.id, "dead_letter", error=str(exc), retry_count=msg.retry_count + 1)
            logger.error("msg %d dead-lettered (HTTP %d)", msg.id, status)
            return
        _retry(msg, exc)
    except Exception as exc:
        logger.warning("msg %d failed: %s", msg.id, exc)
        _retry(msg, exc)


def _retry(msg: QueueMessage, exc: Exception) -> None:
    new_retry = msg.retry_count + 1
    if new_retry >= message_queue.MAX_RETRIES:
        message_queue.set_state(msg.id, "dead_letter", error=str(exc), retry_count=new_retry)
        logger.error("msg %d dead-lettered after %d attempts", msg.id, new_retry)
    else:
        message_queue.set_state(
            msg.id, "queued",
            error=str(exc),
            retry_count=new_retry,
            next_attempt_at=message_queue.next_attempt_iso(new_retry),
        )
        logger.info("msg %d will retry in %ds", msg.id, message_queue.backoff_for(new_retry))


def process_batch() -> None:
    """Process up to 5 queued messages. Called on a fixed interval by the scheduler."""
    items = message_queue.get_queued(limit=5)
    if not items:
        return
    for msg in items:
        _send(msg)
    broadcaster.broadcast("queue", message_queue.get_all())
