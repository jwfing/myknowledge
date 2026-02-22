"""MCP Server with streamable HTTP transport - exposes 3 tools."""

import logging
import time

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from myknowledge.config import settings
from myknowledge.retrieval.embedding import embed_text
from myknowledge.retrieval.search import search_memories
from myknowledge.storage.db import async_session_factory
from myknowledge.storage.repository import Repository

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "myknowledge",
    host=settings.MCP_HOST,
    port=settings.MCP_PORT,
    instructions=(
        "Agent Memory service for cross-project knowledge sharing. "
        "Use `query_memory` to search for relevant knowledge across all projects. "
        "Use `remember_this` to save important knowledge for future reference. "
        "Use `list_projects` to see all projects and their knowledge overview."
    ),
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming HTTP request with headers and response status."""

    async def dispatch(self, request: Request, call_next):
        req_logger = logging.getLogger("myknowledge.mcp.http")
        start = time.monotonic()

        # Log request details
        req_logger.info(
            ">>> %s %s from %s  Content-Type: %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
            request.headers.get("content-type", "none"),
        )
        req_logger.debug(
            "    Headers: %s",
            dict(request.headers),
        )

        try:
            response: Response = await call_next(request)
            elapsed = (time.monotonic() - start) * 1000
            req_logger.info(
                "<<< %s %s -> %d (%.1fms)",
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )
            return response
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            req_logger.error(
                "<<< %s %s -> ERROR (%.1fms): %s",
                request.method,
                request.url.path,
                elapsed,
                e,
                exc_info=True,
            )
            raise


def create_mcp_app():
    """Create the ASGI app from FastMCP with logging middleware."""
    app = mcp.streamable_http_app()
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("MCP ASGI app created with request logging middleware")
    return app


# ── Tool 1: remember_this ──


@mcp.tool()
async def remember_this(
    content: str,
    memory_type: str,
    project_name: str | None = None,
    tags: list[str] | None = None,
    importance: float = 0.8,
) -> str:
    """Save an important knowledge snippet for future cross-project reference.

    Args:
        content: The knowledge to remember (clear, self-contained description)
        memory_type: Type of memory - "semantic" (facts/APIs), "episodic" (experiences/bugs), or "procedural" (workflows/conventions)
        project_name: Project this knowledge belongs to (optional)
        tags: Technology/domain tags for better retrieval (optional)
        importance: Importance score 0-1, default 0.8 for actively saved memories
    """
    logger.info(
        "remember_this called: memory_type=%s, project=%s, tags=%s, importance=%s, content_len=%d",
        memory_type, project_name, tags, importance, len(content),
    )

    if memory_type not in ("semantic", "episodic", "procedural"):
        logger.warning("Invalid memory_type: %s", memory_type)
        return f"Error: memory_type must be 'semantic', 'episodic', or 'procedural', got '{memory_type}'"

    try:
        embedding = embed_text(content)
        logger.debug("Embedding generated, dims=%d", len(embedding))

        async with async_session_factory() as session:
            repo = Repository(session)

            # Resolve project
            project_id = None
            if project_name:
                project = await repo.get_or_create_project(project_name)
                project_id = project.id
                logger.info("Resolved project '%s' -> %s", project_name, project_id)

            # Dedup check
            existing = await repo.find_similar_memory(
                embedding=embedding,
                threshold=settings.DEDUP_SIMILARITY_THRESHOLD,
            )
            if existing:
                if importance > existing.importance:
                    await repo.update_memory(
                        existing,
                        content=content,
                        embedding=embedding,
                        importance=importance,
                        tags=list(set((existing.tags or []) + (tags or []))),
                    )
                    await session.commit()
                    logger.info("Updated existing memory %s (importance: %s -> %s)", existing.id, existing.importance, importance)
                    return f"Updated existing memory {existing.id} (higher importance: {importance})"
                logger.info("Dedup hit: similar memory %s already exists (importance: %s)", existing.id, existing.importance)
                return f"Similar memory already exists: {existing.id} (importance: {existing.importance})"

            # Create new
            memory = await repo.create_memory(
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                importance=importance,
                project_id=project_id,
                tags=tags or [],
            )
            await session.commit()
            logger.info("Memory saved: %s (type=%s, importance=%s)", memory.id, memory_type, importance)
            return f"Memory saved: {memory.id} (type={memory_type}, importance={importance})"

    except Exception as e:
        logger.error("Failed to save memory: %s", e, exc_info=True)
        return f"Error saving memory: {str(e)}"


# ── Tool 2: query_memory ──


@mcp.tool()
async def query_memory(
    query: str,
    project_name: str | None = None,
    memory_types: list[str] | None = None,
    limit: int = 3,
) -> str:
    """Search across all saved memories using semantic similarity.

    Returns the most relevant knowledge fragments from all projects.

    Args:
        query: Natural language search query (e.g., "How does the OAuth API work in the platform project?")
        project_name: Filter results to a specific project (optional)
        memory_types: Filter by types: "semantic", "episodic", "procedural" (optional)
        limit: Max results to return, 1-5, default 3
    """
    limit = max(1, min(5, limit))
    logger.info(
        "query_memory called: query='%s', project=%s, types=%s, limit=%d",
        query[:80], project_name, memory_types, limit,
    )

    try:
        async with async_session_factory() as session:
            # Resolve project_id
            project_id = None
            if project_name:
                repo = Repository(session)
                project = await repo.get_project_by_name(project_name)
                if project:
                    project_id = project.id
                    logger.info("Resolved project '%s' -> %s", project_name, project_id)
                else:
                    logger.warning("Project '%s' not found, searching all projects", project_name)

            result = await search_memories(
                session=session,
                query=query,
                project_id=project_id,
                memory_types=memory_types,
                limit=limit,
            )

        if not result.results:
            logger.info("query_memory: no results found")
            return "No relevant memories found."

        logger.info("query_memory: found %d results (total_found=%d)", len(result.results), result.total_found)

        # Format results for the agent
        lines = [f"Found {result.total_found} relevant memories (showing top {len(result.results)}):\n"]
        for i, mem in enumerate(result.results, 1):
            project_label = f" [{mem.project_name}]" if mem.project_name else ""
            lines.append(
                f"{i}. [{mem.memory_type}]{project_label} (score: {mem.score:.2f})\n"
                f"   {mem.content}\n"
                f"   Tags: {', '.join(mem.tags) if mem.tags else 'none'}"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error("Failed to query memories: %s", e, exc_info=True)
        return f"Error querying memories: {str(e)}"


# ── Tool 3: list_projects ──


@mcp.tool()
async def list_projects() -> str:
    """List all projects and their knowledge summary.

    Returns an overview of all tracked projects with memory counts and tech stacks.
    """
    logger.info("list_projects called")

    try:
        async with async_session_factory() as session:
            repo = Repository(session)
            projects = await repo.list_projects_with_counts()

        if not projects:
            logger.info("list_projects: no projects found")
            return "No projects found. Start by saving memories with remember_this or ingesting conversations."

        logger.info("list_projects: returning %d projects", len(projects))

        lines = [f"Total projects: {len(projects)}\n"]
        for p in projects:
            proj = p["project"]
            count = p["memory_count"]
            tech = ", ".join(proj.tech_stack) if proj.tech_stack else "not specified"
            desc = proj.description or "No description"
            lines.append(
                f"- {proj.name} ({count} memories)\n"
                f"  Tech: {tech}\n"
                f"  Description: {desc}"
            )

        return "\n".join(lines)

    except Exception as e:
        logger.error("Failed to list projects: %s", e, exc_info=True)
        return f"Error listing projects: {str(e)}"
