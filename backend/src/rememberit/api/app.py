"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rememberit.api.routes.dashboard import router as dashboard_router
from rememberit.api.routes.health import router as health_router
from rememberit.api.routes.ingest import router as ingest_router
from rememberit.config import settings
from rememberit.mcp.server import create_mcp_app

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    mcp_app = create_mcp_app()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup and shutdown events."""
        # Startup: pre-load the embedding model
        logger.info("Loading embedding model...")
        from rememberit.retrieval.embedding import get_model

        get_model()
        logger.info("Embedding model ready.")

        # Initialize the MCP session manager (sub-app lifespan
        # doesn't run automatically when mounted inside FastAPI)
        async with mcp_app.router.lifespan_context(mcp_app):
            yield

        logger.info("Shutting down.")

    app = FastAPI(
        title="rememberit",
        description="Agent Memory - Cross-project knowledge sharing",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.API_PREFIX)
    app.include_router(ingest_router, prefix=settings.API_PREFIX)
    app.include_router(dashboard_router, prefix=settings.API_PREFIX)

    # Mount MCP server at /mcp
    app.mount("/mcp", mcp_app)

    return app


app = create_app()
