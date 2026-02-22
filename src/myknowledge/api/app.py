"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from myknowledge.api.routes.health import router as health_router
from myknowledge.api.routes.ingest import router as ingest_router
from myknowledge.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: pre-load the embedding model
    logger.info("Loading embedding model...")
    from myknowledge.retrieval.embedding import get_model

    get_model()
    logger.info("Embedding model ready.")
    yield
    # Shutdown
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="myknowledge",
        description="Agent Memory - Cross-project knowledge sharing",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health_router, prefix=settings.API_PREFIX)
    app.include_router(ingest_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
