"""Dashboard API endpoints for the frontend."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rememberit.storage.db import get_session
from rememberit.storage.models import Entity, Memory, MemoryEntityLink, Project, Relation

router = APIRouter(tags=["dashboard"])


@router.get("/memories")
async def list_memories(
    memory_type: str | None = None,
    project_id: uuid.UUID | None = None,
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Memory)
        .options(selectinload(Memory.project))
        .order_by(Memory.created_at.desc())
        .limit(limit)
    )
    if memory_type:
        stmt = stmt.where(Memory.memory_type == memory_type)
    if project_id:
        stmt = stmt.where(Memory.project_id == project_id)
    if search:
        stmt = stmt.where(Memory.content.ilike(f"%{search}%"))

    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "content": m.content,
            "memory_type": m.memory_type,
            "importance": m.importance,
            "project_id": str(m.project_id) if m.project_id else None,
            "tags": m.tags,
            "source_session_id": m.source_session_id,
            "created_at": m.created_at.isoformat(),
            "updated_at": m.updated_at.isoformat(),
            "project": {"name": m.project.name} if m.project else None,
        }
        for m in rows
    ]


@router.get("/memory-stats")
async def memory_stats(session: AsyncSession = Depends(get_session)):
    memories_result = await session.execute(select(Memory.memory_type))
    types = [row[0] for row in memories_result.all()]

    projects_result = await session.execute(
        select(Project).order_by(Project.name.asc())
    )
    projects = projects_result.scalars().all()

    return {
        "total": len(types),
        "semantic": types.count("semantic"),
        "episodic": types.count("episodic"),
        "procedural": types.count("procedural"),
        "projects": [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "tech_stack": p.tech_stack,
                "created_at": p.created_at.isoformat(),
            }
            for p in projects
        ],
    }


@router.get("/entities")
async def list_entities(
    project_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Entity).options(selectinload(Entity.project))
    if project_id:
        stmt = stmt.where(Entity.project_id == project_id)
    if entity_type:
        stmt = stmt.where(Entity.entity_type == entity_type)

    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "entity_type": e.entity_type,
            "project_id": str(e.project_id) if e.project_id else None,
            "description": e.description,
            "project": {"name": e.project.name} if e.project else None,
        }
        for e in rows
    ]


@router.get("/relations")
async def list_relations(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Relation))
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "source_entity_id": str(r.source_entity_id),
            "target_entity_id": str(r.target_entity_id),
            "relation_type": r.relation_type,
            "description": r.description,
        }
        for r in rows
    ]


@router.get("/graph-stats")
async def graph_stats(session: AsyncSession = Depends(get_session)):
    entities_result = await session.execute(select(Entity.entity_type))
    entity_types = [row[0] for row in entities_result.all()]

    relations_count = await session.execute(select(func.count(Relation.id)))

    entity_type_counts: dict[str, int] = {}
    for t in entity_types:
        entity_type_counts[t] = entity_type_counts.get(t, 0) + 1

    return {
        "totalEntities": len(entity_types),
        "totalRelations": relations_count.scalar() or 0,
        "entityTypeCounts": entity_type_counts,
    }


@router.get("/entity-memories/{entity_id}")
async def entity_memories(
    entity_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Memory)
        .join(MemoryEntityLink, MemoryEntityLink.memory_id == Memory.id)
        .where(MemoryEntityLink.entity_id == entity_id)
        .limit(20)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "content": m.content,
            "memory_type": m.memory_type,
            "importance": m.importance,
            "created_at": m.created_at.isoformat(),
        }
        for m in rows
    ]
