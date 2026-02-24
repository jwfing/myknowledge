"""Data access layer for all database operations."""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from myknowledge.storage.models import (
    Conversation,
    Entity,
    Memory,
    MemoryEntityLink,
    Project,
    Relation,
)


class Repository:
    """Unified repository for all database CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Projects ──

    async def get_or_create_project(self, name: str, **kwargs) -> Project:
        """Get a project by name, or create it if it doesn't exist."""
        stmt = select(Project).where(Project.name == name)
        result = await self.session.execute(stmt)
        project = result.scalar_one_or_none()
        if project is None:
            project = Project(name=name, **kwargs)
            self.session.add(project)
            await self.session.flush()
        return project

    async def get_project_by_name(self, name: str) -> Project | None:
        stmt = select(Project).where(Project.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_projects_with_counts(self) -> list[dict]:
        """List all projects with their memory counts."""
        stmt = (
            select(
                Project,
                func.count(Memory.id).label("memory_count"),
            )
            .outerjoin(Memory, Memory.project_id == Project.id)
            .group_by(Project.id)
            .order_by(Project.created_at.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {
                "project": row[0],
                "memory_count": row[1],
            }
            for row in rows
        ]

    # ── Memories ──

    async def create_memory(
        self,
        content: str,
        embedding: list[float],
        memory_type: str,
        importance: float = 0.5,
        project_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        source_session_id: str | None = None,
    ) -> Memory:
        memory = Memory(
            content=content,
            embedding=embedding,
            memory_type=memory_type,
            importance=importance,
            project_id=project_id,
            tags=tags or [],
            source_session_id=source_session_id,
        )
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def search_memories_by_vector(
        self,
        query_embedding: list[float],
        limit: int = 5,
        project_id: uuid.UUID | None = None,
        memory_types: list[str] | None = None,
        similarity_threshold: float = 0.3,
    ) -> list[dict]:
        """Vector similarity search with optional filters."""
        # Build cosine distance expression
        distance_expr = Memory.embedding.cosine_distance(query_embedding)
        similarity_expr = (1 - distance_expr).label("similarity")

        stmt = select(Memory, similarity_expr).options(
            selectinload(Memory.project)
        ).where(
            (1 - distance_expr) >= similarity_threshold
        )

        if project_id:
            stmt = stmt.where(Memory.project_id == project_id)
        if memory_types:
            stmt = stmt.where(Memory.memory_type.in_(memory_types))

        stmt = stmt.order_by(distance_expr.asc()).limit(limit)

        result = await self.session.execute(stmt)
        rows = result.all()
        return [{"memory": row[0], "similarity": float(row[1])} for row in rows]

    async def find_similar_memory(
        self,
        embedding: list[float],
        threshold: float = 0.9,
    ) -> Memory | None:
        """Find an existing memory that is very similar (for deduplication)."""
        distance_expr = Memory.embedding.cosine_distance(embedding)
        stmt = (
            select(Memory)
            .where((1 - distance_expr) >= threshold)
            .order_by(distance_expr.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_memory(self, memory: Memory, **kwargs) -> Memory:
        for key, value in kwargs.items():
            setattr(memory, key, value)
        memory.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return memory

    # ── Entities ──

    async def get_or_create_entity(
        self,
        name: str,
        entity_type: str,
        project_id: uuid.UUID | None = None,
        **kwargs,
    ) -> Entity:
        stmt = select(Entity).where(
            Entity.name == name,
            Entity.entity_type == entity_type,
            Entity.project_id == project_id,
        )
        result = await self.session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            entity = Entity(
                name=name,
                entity_type=entity_type,
                project_id=project_id,
                **kwargs,
            )
            self.session.add(entity)
            await self.session.flush()
        return entity

    async def get_entities_by_project(self, project_id: uuid.UUID) -> list[Entity]:
        stmt = select(Entity).where(Entity.project_id == project_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_related_memories_via_entity(
        self, entity_name: str, limit: int = 5
    ) -> list[Memory]:
        """Find memories linked to a specific entity by name."""
        stmt = (
            select(Memory)
            .join(MemoryEntityLink, MemoryEntityLink.memory_id == Memory.id)
            .join(Entity, Entity.id == MemoryEntityLink.entity_id)
            .where(Entity.name.ilike(f"%{entity_name}%"))
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Relations ──

    async def create_relation(
        self,
        source_entity_id: uuid.UUID,
        target_entity_id: uuid.UUID,
        relation_type: str,
        description: str | None = None,
    ) -> Relation:
        # Upsert: skip if already exists
        stmt = select(Relation).where(
            Relation.source_entity_id == source_entity_id,
            Relation.target_entity_id == target_entity_id,
            Relation.relation_type == relation_type,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        relation = Relation(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relation_type=relation_type,
            description=description,
        )
        self.session.add(relation)
        await self.session.flush()
        return relation

    # ── Memory-Entity Links ──

    async def link_memory_to_entity(
        self, memory_id: uuid.UUID, entity_id: uuid.UUID
    ) -> MemoryEntityLink:
        # Upsert: skip if already exists
        stmt = select(MemoryEntityLink).where(
            MemoryEntityLink.memory_id == memory_id,
            MemoryEntityLink.entity_id == entity_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        link = MemoryEntityLink(memory_id=memory_id, entity_id=entity_id)
        self.session.add(link)
        await self.session.flush()
        return link

    # ── Conversations ──

    async def get_conversation_by_session_id(self, session_id: str) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_conversation(
        self,
        session_id: str,
        raw_content: dict,
        project_id: uuid.UUID | None = None,
    ) -> Conversation:
        conversation = Conversation(
            session_id=session_id,
            raw_content=raw_content,
            project_id=project_id,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_unprocessed_conversations(self, limit: int = 10) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.processed == False)
            .order_by(Conversation.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_conversation_processed(self, conversation_id: uuid.UUID) -> None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one()
        conversation.processed = True
        conversation.processed_at = datetime.now(timezone.utc)
        await self.session.flush()
