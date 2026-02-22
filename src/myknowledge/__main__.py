"""Entry point: run API server or MCP server."""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def run_api():
    """Run the FastAPI REST API server."""
    import uvicorn
    from myknowledge.config import settings

    uvicorn.run(
        "myknowledge.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )


def run_mcp():
    """Run the MCP server with streamable HTTP transport."""
    # Enable DEBUG for MCP/uvicorn to trace invalid HTTP requests
    logging.getLogger("mcp").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.error").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

    from myknowledge.mcp.server import create_mcp_app

    # Pre-load embedding model
    from myknowledge.retrieval.embedding import get_model
    get_model()

    app = create_mcp_app()

    import uvicorn
    from myknowledge.config import settings

    logger = logging.getLogger("myknowledge.mcp.startup")
    logger.info(
        "Starting MCP server on %s:%s (endpoint: /mcp)",
        settings.MCP_HOST,
        settings.MCP_PORT,
    )

    uvicorn.run(
        app,
        host=settings.MCP_HOST,
        port=settings.MCP_PORT,
        log_level="debug",
    )


def main():
    parser = argparse.ArgumentParser(description="myknowledge - Agent Memory")
    parser.add_argument(
        "command",
        choices=["api", "mcp"],
        help="Which server to run: 'api' for REST API, 'mcp' for MCP server",
    )
    args = parser.parse_args()

    if args.command == "api":
        run_api()
    elif args.command == "mcp":
        run_mcp()


if __name__ == "__main__":
    main()
