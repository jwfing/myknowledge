"""Entry point: run the unified server (API + MCP)."""

import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def run_server():
    """Run the unified server with both REST API and MCP endpoints."""
    import uvicorn
    from rememberit.config import settings

    logger = logging.getLogger("rememberit.startup")
    logger.info(
        "Starting rememberit on %s:%s (API: %s/*, MCP: /mcp)",
        settings.API_HOST,
        settings.API_PORT,
        settings.API_PREFIX,
    )

    uvicorn.run(
        "rememberit.api.app:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
    )


def main():
    parser = argparse.ArgumentParser(description="rememberit - Agent Memory")
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        choices=["serve"],
        help="Command to run (default: serve)",
    )
    args = parser.parse_args()

    run_server()


if __name__ == "__main__":
    main()
