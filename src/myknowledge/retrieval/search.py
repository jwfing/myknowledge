"""Hybrid search: vector similarity + entity-based retrieval."""

import logging
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from myknowledge.config import settings
from myknowledge.retrieval.embedding import embed_text
from myknowledge.retrieval.scorer import calculate_score
from myknowledge.storage.repository import Repository
from myknowledge.types import MemoryResponse, QueryResponse

logger = logging.getLogger(__name__)


async def search_memories(
    session: AsyncSession,
    query: str,
    project_id: uuid.UUID | None = None,
    memory_types: list[str] | None = None,
    limit: int = 3,
) -> QueryResponse:
    """
    Hybrid search combining vector similarity with entity-based retrieval.

    1. Generate query embedding
    2. Vector search in memories table
    3. Score results with 3-dimensional scoring
    4. Return top-k results within token budget
    """
    start = time.monotonic()
    repo = Repository(session)

    # Step 1: Generate query embedding
    query_embedding = embed_text(query)

    # Step 2: Vector similarity search
    raw_results = await repo.search_memories_by_vector(
        query_embedding=query_embedding,
        limit=limit * 2,  # Fetch more, then re-rank
        project_id=project_id,
        memory_types=memory_types,
        similarity_threshold=settings.SIMILARITY_THRESHOLD,
    )

    # Step 3: Re-score with 3-dimensional scoring
    scored_results = []
    for row in raw_results:
        memory = row["memory"]
        similarity = row["similarity"]
        score = calculate_score(
            similarity=similarity,
            importance=memory.importance,
            created_at=memory.created_at,
        )
        scored_results.append({"memory": memory, "score": score, "similarity": similarity})

    # Sort by composite score
    scored_results.sort(key=lambda x: x["score"], reverse=True)

    # Step 4: Trim to limit and token budget
    final_results = []
    total_tokens_estimate = 0
    for row in scored_results[:limit]:
        memory = row["memory"]
        # Rough token estimate: ~4 chars per token
        token_estimate = len(memory.content) // 4
        if total_tokens_estimate + token_estimate > settings.MAX_TOKENS_PER_QUERY:
            break
        total_tokens_estimate += token_estimate

        # Resolve project name
        project_name = None
        if memory.project:
            project_name = memory.project.name

        final_results.append(
            MemoryResponse(
                id=memory.id,
                content=memory.content,
                memory_type=memory.memory_type,
                importance=memory.importance,
                project_name=project_name,
                tags=memory.tags or [],
                created_at=memory.created_at,
                score=row["score"],
            )
        )

    elapsed_ms = (time.monotonic() - start) * 1000
    return QueryResponse(
        results=final_results,
        total_found=len(raw_results),
        query_time_ms=round(elapsed_ms, 1),
    )
