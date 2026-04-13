"""FastAPI application entry point."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import alerts, queue, sim, webhook, ws
from services import broadcaster, linq_client, message_queue, poller, sender

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 30


async def _run_poller() -> None:
    while True:
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(poller.tick)
        except Exception:
            logger.exception("poller error")


async def _run_queue_processor(work_event: asyncio.Event) -> None:
    while True:
        await work_event.wait()
        work_event.clear()
        try:
            await asyncio.to_thread(sender.process_batch)
        except Exception:
            logger.exception("sender error")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    loop = asyncio.get_running_loop()
    broadcaster.set_loop(loop)
    work_event = asyncio.Event()
    message_queue.init(loop, work_event)
    await asyncio.to_thread(poller.tick)  # evaluate existing alerts immediately on startup
    logger.info("DB initialised, broadcaster ready")

    tasks = [
        asyncio.create_task(_run_poller(), name="poller"),
        asyncio.create_task(_run_queue_processor(work_event), name="queue-processor"),
    ]
    logger.info("Background tasks started")

    yield

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    linq_client.close()
    logger.info("Shutdown complete")


app = FastAPI(title="Linq Alert API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(ws.router)
app.include_router(alerts.router)
app.include_router(queue.router)
app.include_router(sim.router)
