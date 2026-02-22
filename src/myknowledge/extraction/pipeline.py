"""Async extraction pipeline: conversation → structured knowledge."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from myknowledge.config import settings
from myknowledge.extraction.llm_client import extract_knowledge
from myknowledge.retrieval.embedding import embed_text
from myknowledge.storage.db import async_session_factory
from myknowledge.storage.repository import Repository
from myknowledge.types import ExtractedKnowledge

logger = logging.getLogger(__name__)


def _conversation_to_text(messages: list[dict]) -> str:
    """Convert raw message list to readable text for the LLM."""
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            # Handle structured content (e.g., tool calls)
            content = " ".join(
                part.get("text", str(part)) for part in content if isinstance(part, dict)
            )
        lines.append(f"[{role}]: {content}")
    return "\n\n".join(lines)


def _segment_conversation(text: str, max_chars: int = 8000) -> list[str]:
    """Split a long conversation into segments by topic/length.

    For MVP, we simply split by character length at paragraph boundaries.
    A more sophisticated version could use LLM-based topic segmentation.
    """
    if len(text) <= max_chars:
        return [text]

    segments = []
    paragraphs = text.split("\n\n")
    current_segment = ""

    for para in paragraphs:
        if len(current_segment) + len(para) + 2 > max_chars and current_segment:
            segments.append(current_segment.strip())
            current_segment = para
        else:
            current_segment += "\n\n" + para if current_segment else para

    if current_segment.strip():
        segments.append(current_segment.strip())

    return segments


async def process_conversation(conversation_id: uuid.UUID) -> None:
    """
    Main extraction pipeline:
    1. Fetch raw conversation from DB
    2. Convert to text and segment
    3. Extract knowledge via LLM
    4. Generate embeddings
    5. Deduplicate against existing memories
    6. Store memories, entities, relations, and links
    7. Mark conversation as processed
    """
    async with async_session_factory() as session:
        repo = Repository(session)

        try:
            # Step 1: Fetch conversation
            from sqlalchemy import select
            from myknowledge.storage.models import Conversation

            stmt = select(Conversation).where(Conversation.id == conversation_id)
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation is None:
                logger.error("Conversation %s not found", conversation_id)
                return
            if conversation.processed:
                logger.info("Conversation %s already processed", conversation_id)
                return

            # Step 2: Convert and segment
            messages = conversation.raw_content.get("messages", conversation.raw_content)
            if isinstance(messages, dict):
                messages = [messages]
            text = _conversation_to_text(messages)
            segments = _segment_conversation(text)

            logger.info(
                "Processing conversation %s: %d segments",
                conversation_id,
                len(segments),
            )

            # Step 3-6: Process each segment
            total_memories = 0
            for i, segment in enumerate(segments):
                logger.info("Extracting from segment %d/%d", i + 1, len(segments))
                fragments = await extract_knowledge(segment)

                for fragment in fragments:
                    memory = await _store_fragment(
                        repo=repo,
                        fragment=fragment,
                        project_id=conversation.project_id,
                        source_session_id=conversation.session_id,
                    )
                    if memory:
                        total_memories += 1

            # Step 7: Mark as processed
            await repo.mark_conversation_processed(conversation_id)
            await session.commit()

            logger.info(
                "Conversation %s processed: %d memories created",
                conversation_id,
                total_memories,
            )

        except Exception as e:
            logger.error("Failed to process conversation %s: %s", conversation_id, e)
            await session.rollback()
            raise


async def _store_fragment(
    repo: Repository,
    fragment: ExtractedKnowledge,
    project_id: uuid.UUID | None,
    source_session_id: str | None,
) -> object | None:
    """Store a single extracted knowledge fragment with deduplication."""
    # Generate embedding
    embedding = embed_text(fragment.content)

    # Deduplication check
    existing = await repo.find_similar_memory(
        embedding=embedding,
        threshold=settings.DEDUP_SIMILARITY_THRESHOLD,
    )
    if existing:
        # Update existing memory if new one is more important
        if fragment.importance > existing.importance:
            await repo.update_memory(
                existing,
                content=fragment.content,
                embedding=embedding,
                importance=fragment.importance,
                tags=list(set((existing.tags or []) + fragment.tags)),
            )
            logger.info("Updated existing memory %s (higher importance)", existing.id)
        return None

    # Create new memory
    memory = await repo.create_memory(
        content=fragment.content,
        embedding=embedding,
        memory_type=fragment.memory_type.value,
        importance=fragment.importance,
        project_id=project_id,
        tags=fragment.tags,
        source_session_id=source_session_id,
    )

    # Create entities and links
    entity_map = {}
    for ent_data in fragment.entities:
        entity = await repo.get_or_create_entity(
            name=ent_data["name"],
            entity_type=ent_data.get("type", "Component"),
            project_id=project_id,
        )
        entity_map[ent_data["name"]] = entity
        await repo.link_memory_to_entity(memory.id, entity.id)

    # Create relations
    for rel_data in fragment.relations:
        source = entity_map.get(rel_data.get("source"))
        target = entity_map.get(rel_data.get("target"))
        if source and target:
            await repo.create_relation(
                source_entity_id=source.id,
                target_entity_id=target.id,
                relation_type=rel_data.get("type", "uses"),
            )

    return memory
