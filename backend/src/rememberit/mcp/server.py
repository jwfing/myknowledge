"""MCP Server with streamable HTTP transport - exposes 3 tools."""

import logging
import time

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from rememberit.config import settings
from rememberit.retrieval.embedding import embed_text
from rememberit.retrieval.search import search_memories
from rememberit.storage.db import async_session_factory
from rememberit.storage.repository import Repository

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "rememberit",
    instructions=(
        "RememberIt — Agent Memory for cross-project knowledge sharing.\n\n"
        "IMPORTANT USAGE GUIDELINES:\n"
        "1. PROACTIVELY SEARCH before starting work on any non-trivial task. "
        "Call `recall_memory` at the beginning of a conversation when the user describes "
        "their goal, to check if relevant knowledge exists from past sessions or other projects. "
        "This is especially important for: API integrations, architecture decisions, "
        "debugging patterns, configuration setups, and deployment procedures.\n"
        "2. SAVE valuable knowledge with `remember_it` when you discover something "
        "worth remembering: a non-obvious solution, an architecture decision with rationale, "
        "a debugging insight, or a team convention. Don't save routine code changes.\n"
        "3. Use `list_projects` to understand what knowledge domains are available.\n\n"
        "Think of this as your long-term memory across projects. "
        "If you've seen a similar problem before, search first — don't reinvent the wheel."
    ),
    stateless_http=True,
    streamable_http_path="/",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming HTTP request with headers and response status."""

    async def dispatch(self, request: Request, call_next):
        req_logger = logging.getLogger("rememberit.mcp.http")
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


# ── Tool 1: remember_it ──


@mcp.tool()
async def remember_it(
    content: str,
    memory_type: str,
    project_name: str | None = None,
    tags: list[str] | None = None,
    importance: float = 0.8,
) -> str:
    """Save an important knowledge snippet for future cross-project reference.

    Call this when you discover something worth remembering for future sessions:
    - Architecture decisions and their rationale
    - Non-obvious solutions to tricky problems
    - API contracts, endpoint behaviors, or integration patterns
    - Debugging insights (root cause + fix for non-trivial bugs)
    - Team conventions or project-specific workflows

    Do NOT save: routine code changes, trivial fixes, or well-known information.

    Args:
        content: The knowledge to remember — must be a clear, self-contained description
            that would be useful to someone unfamiliar with the current conversation.
        memory_type: "semantic" (facts, API specs, definitions), "episodic" (debugging
            experiences, problems encountered and solutions), or "procedural" (workflows,
            conventions, step-by-step processes)
        project_name: Project this knowledge belongs to (optional, auto-detected if not set)
        tags: Technology/domain tags for better retrieval, e.g. ["OAuth", "PostgreSQL"] (optional)
        importance: Score 0-1. Use 0.9 for key architectural decisions, 0.7 for useful
            patterns, 0.5 for general context. Default 0.8.
    """
    logger.info(
        "remember_it called: memory_type=%s, project=%s, tags=%s, importance=%s, content_len=%d",
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


# ── Tool 2: recall_memory ──


@mcp.tool()
async def recall_memory(
    query: str,
    project_name: str | None = None,
    memory_types: list[str] | None = None,
    limit: int = 3,
) -> str:
    """Search across all saved memories from past sessions and other projects.

    WHEN TO USE: Call this proactively at the start of a task, especially when:
    - The user asks about APIs, integrations, or system architecture
    - You're about to solve a problem that might have been solved before
    - The task involves configuration, deployment, or infrastructure
    - You're working on a project that might share patterns with other projects
    - The user references past work ("like we did before", "the same pattern")

    Returns the most relevant knowledge fragments ranked by semantic similarity,
    importance, and recency.

    Args:
        query: Natural language search query describing what you need to know.
            Be specific — "OAuth PKCE flow token endpoint" works better than "OAuth".
        project_name: Filter to a specific project (optional — omit to search all projects)
        memory_types: Filter by types: "semantic", "episodic", "procedural" (optional)
        limit: Max results to return, 1-5, default 3
    """
    limit = max(1, min(5, limit))
    logger.info(
        "recall_memory called: query='%s', project=%s, types=%s, limit=%d",
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
            logger.info("recall_memory: no results found")
            return "No relevant memories found."

        logger.info("recall_memory: found %d results (total_found=%d)", len(result.results), result.total_found)

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
            return "No projects found. Start by saving memories with remember_it or ingesting conversations."

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
