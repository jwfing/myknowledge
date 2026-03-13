"""Async extraction pipeline: conversation → structured knowledge."""

import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from rememberit.config import settings
from rememberit.extraction.llm_client import extract_knowledge
from rememberit.retrieval.embedding import embed_text
from rememberit.storage.db import async_session_factory
from rememberit.storage.repository import Repository
from rememberit.types import ExtractedKnowledge

logger = logging.getLogger(__name__)

# ── Entity noise filter ──

# Patterns that indicate a noisy entity (filenames, generic code artifacts)
_NOISY_ENTITY_PATTERNS = [
    re.compile(r"^.+\.\w{1,5}$"),     # filenames: model.py, config.json, utils.ts
    re.compile(r"^__\w+__$"),          # dunder names: __init__, __main__
    re.compile(r"^[a-z_]{1,15}$"),     # short lowercase identifiers: func, var, cls
    re.compile(r"^\.\w+$"),            # dotfiles: .env, .gitignore
]

# Explicit blocklist of common noisy entity names
_NOISY_ENTITY_NAMES = {
    "function", "variable", "file", "class", "module", "package", "folder",
    "directory", "import", "export", "print", "logging", "error", "exception",
    "os", "sys", "json", "pathlib", "subprocess", "typing", "datetime",
    "main", "index", "app", "test", "utils", "helpers", "config", "settings",
    "readme", "changelog", "license", "makefile", "dockerfile",
    "node_modules", "venv", ".git", "__pycache__",
}


def _is_noisy_entity(name: str) -> bool:
    """Check if an entity name is likely noise rather than a meaningful concept."""
    lower = name.lower().strip()
    if lower in _NOISY_ENTITY_NAMES:
        return True
    for pattern in _NOISY_ENTITY_PATTERNS:
        if pattern.match(lower):
            return True
    return False


def _filter_entities(fragment: ExtractedKnowledge) -> ExtractedKnowledge:
    """Remove noisy entities from a knowledge fragment and clean up orphaned relations."""
    clean_entities = [e for e in fragment.entities if not _is_noisy_entity(e.get("name", ""))]
    valid_names = {e["name"] for e in clean_entities}
    clean_relations = [
        r for r in fragment.relations
        if r.get("source") in valid_names and r.get("target") in valid_names
    ]
    fragment.entities = clean_entities
    fragment.relations = clean_relations
    return fragment


def _trim_code_blocks(text: str, max_lines: int = 20) -> str:
    """Truncate long code blocks to reduce token usage while keeping context."""
    result = []
    in_code = False
    code_lines = []
    for line in text.split("\n"):
        if line.strip().startswith("```") and not in_code:
            in_code = True
            code_lines = [line]
        elif line.strip().startswith("```") and in_code:
            code_lines.append(line)
            if len(code_lines) > max_lines + 2:
                # Keep first and last lines of the code block
                trimmed = code_lines[:max_lines // 2 + 1]
                trimmed.append(f"    ... ({len(code_lines) - max_lines} lines omitted) ...")
                trimmed.extend(code_lines[-(max_lines // 2):])
                result.extend(trimmed)
            else:
                result.extend(code_lines)
            in_code = False
            code_lines = []
        elif in_code:
            code_lines.append(line)
        else:
            result.append(line)
    # Handle unclosed code blocks
    if code_lines:
        result.extend(code_lines[:max_lines])
    return "\n".join(result)


def _conversation_to_text(messages: list[dict]) -> str:
    """Convert raw message list to readable text for the LLM.

    Applies token-reduction optimizations:
    - Strips tool call results (verbose, not useful for knowledge extraction)
    - Truncates long code blocks
    """
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            # Handle structured content — skip tool_use and tool_result blocks
            text_parts = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif part.get("type") == "tool_result":
                        # Include a brief marker instead of full tool output
                        tool_name = part.get("tool_use_id", "tool")
                        text_parts.append(f"[tool result from {tool_name}: omitted for brevity]")
                    # Skip tool_use blocks entirely — the text summary is enough
            content = "\n".join(text_parts)
        if content and content.strip():
            lines.append(f"[{role}]: {_trim_code_blocks(content)}")
    return "\n\n".join(lines)


def _is_trivial_conversation(text: str, message_count: int) -> bool:
    """Pre-filter conversations that are unlikely to contain reusable knowledge.

    Heuristics:
    - Very short conversations (< 500 chars useful text)
    - Too few meaningful exchanges (< 3 assistant messages)
    - Purely routine tasks (simple file edits, one-liner questions)
    """
    # Too short to contain architectural knowledge
    if len(text) < 500:
        return True
    # Very few exchanges
    if message_count < 4:
        return True
    return False


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
            from rememberit.storage.models import Conversation

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

            # Step 2.5: Pre-filter trivial conversations (saves LLM cost)
            if _is_trivial_conversation(text, len(messages)):
                logger.info(
                    "Conversation %s is trivial (%d chars, %d msgs), skipping extraction",
                    conversation_id, len(text), len(messages),
                )
                await repo.mark_conversation_processed(conversation_id)
                await session.commit()
                return

            segments = _segment_conversation(text)

            # Cost control: limit segments to avoid excessive LLM calls
            max_segments = settings.MAX_SEGMENTS_PER_CONVERSATION
            if len(segments) > max_segments:
                logger.info(
                    "Conversation %s has %d segments, capping at %d",
                    conversation_id, len(segments), max_segments,
                )
                segments = segments[:max_segments]

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
                    # Post-process: filter noisy entities
                    fragment = _filter_entities(fragment)
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
