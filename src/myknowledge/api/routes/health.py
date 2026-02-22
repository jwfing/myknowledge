"""Health check endpoint."""

from fastapi import APIRouter

from myknowledge.retrieval.embedding import is_model_loaded
from myknowledge.storage.db import check_connection
from myknowledge.types import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_ok = await check_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="connected" if db_ok else "disconnected",
        embedding_model="loaded" if is_model_loaded() else "not_loaded",
    )
