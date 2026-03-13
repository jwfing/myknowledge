"""Conversation ingest endpoint (Background Path entry point)."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rememberit.extraction.pipeline import process_conversation
from rememberit.storage.db import get_session
from rememberit.storage.repository import Repository
from rememberit.types import ConversationIngestRequest, IngestResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_conversation(
    request: ConversationIngestRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Receive a raw conversation from Claude Code hook and queue it for extraction.

    This is the Background Path entry point. The conversation is stored immediately,
    and extraction happens asynchronously in the background.
    """
    repo = Repository(session)
    new_content = {"messages": request.messages, "metadata": request.metadata}

    # Check for existing conversation with same session_id
    existing = await repo.get_conversation_by_session_id(request.session_id)
    if existing:
        # Upsert: update raw_content with the latest (more complete) transcript
        existing.raw_content = new_content
        if existing.processed:
            # Already extracted — reset so the fuller transcript gets re-processed
            existing.processed = False
            existing.processed_at = None
            await session.commit()
            background_tasks.add_task(process_conversation, existing.id)
            logger.info(
                "Session %s re-queued for extraction (was already processed, got %d messages now)",
                request.session_id, len(request.messages),
            )
            return IngestResponse(
                conversation_id=existing.id,
                status="re-queued",
                message="Updated with newer transcript and re-queued for extraction.",
            )
        else:
            # Not yet processed — just update content, extraction will pick up latest
            await session.commit()
            logger.info(
                "Session %s updated with %d messages (extraction pending)",
                request.session_id, len(request.messages),
            )
            return IngestResponse(
                conversation_id=existing.id,
                status="updated",
                message="Transcript updated, extraction still pending.",
            )

    # Resolve project
    project_id = None
    if request.project_name:
        project = await repo.get_or_create_project(request.project_name)
        project_id = project.id

    # Store new conversation
    conversation = await repo.create_conversation(
        session_id=request.session_id,
        raw_content=new_content,
        project_id=project_id,
    )
    await session.commit()

    # Queue background extraction
    background_tasks.add_task(process_conversation, conversation.id)

    logger.info("Conversation %s queued for extraction (session: %s)", conversation.id, request.session_id)

    return IngestResponse(
        conversation_id=conversation.id,
        status="queued",
        message="Conversation queued for extraction.",
    )
