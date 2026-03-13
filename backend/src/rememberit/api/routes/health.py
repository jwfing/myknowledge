"""Health check endpoint."""

import time

from fastapi import APIRouter

from rememberit.retrieval.embedding import is_model_loaded
from rememberit.storage.db import check_connection
from rememberit.types import HealthResponse

router = APIRouter(tags=["health"])

_start_time = time.monotonic()


def _format_uptime() -> str:
    elapsed = int(time.monotonic() - _start_time)
    parts = []
    for unit, div in [("d", 86400), ("h", 3600), ("m", 60)]:
        if elapsed >= div:
            parts.append(f"{elapsed // div}{unit}")
            elapsed %= div
    parts.append(f"{elapsed}s")
    return " ".join(parts)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_ok = await check_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version="0.1.0",
        uptime=_format_uptime(),
        database="connected" if db_ok else "disconnected",
        embedding_model="loaded" if is_model_loaded() else "not_loaded",
    )
