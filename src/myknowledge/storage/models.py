"""SQLAlchemy ORM models for all database tables."""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Projects ──


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relationships
    memories: Mapped[list["Memory"]] = relationship(back_populates="project", cascade="all, delete")
    entities: Mapped[list["Entity"]] = relationship(back_populates="project", cascade="all, delete")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="project", cascade="all, delete"
    )


# ── Memories ──


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE")
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    source_session_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="memories")
    entity_links: Mapped[list["MemoryEntityLink"]] = relationship(
        back_populates="memory", cascade="all, delete"
    )

    __table_args__ = (
        Index("idx_memories_embedding", "embedding", postgresql_using="ivfflat"),
        Index("idx_memories_tags", "tags", postgresql_using="gin"),
        Index("idx_memories_project_id", "project_id"),
        Index("idx_memories_created_at", "created_at"),
    )


# ── Entities ──


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE")
    )
    description: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="entities")
    memory_links: Mapped[list["MemoryEntityLink"]] = relationship(
        back_populates="entity", cascade="all, delete"
    )
    outgoing_relations: Mapped[list["Relation"]] = relationship(
        foreign_keys="Relation.source_entity_id", back_populates="source_entity", cascade="all, delete"
    )
    incoming_relations: Mapped[list["Relation"]] = relationship(
        foreign_keys="Relation.target_entity_id", back_populates="target_entity", cascade="all, delete"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", "entity_type", name="uq_entity_project_name_type"),
        Index("idx_entities_project_id", "project_id"),
        Index("idx_entities_type", "entity_type"),
    )


# ── Relations ──


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    # Relationships
    source_entity: Mapped[Entity] = relationship(
        foreign_keys=[source_entity_id], back_populates="outgoing_relations"
    )
    target_entity: Mapped[Entity] = relationship(
        foreign_keys=[target_entity_id], back_populates="incoming_relations"
    )

    __table_args__ = (
        UniqueConstraint(
            "source_entity_id", "target_entity_id", "relation_type",
            name="uq_relation_src_tgt_type",
        ),
        Index("idx_relations_source", "source_entity_id"),
        Index("idx_relations_target", "target_entity_id"),
    )


# ── Memory-Entity Links ──


class MemoryEntityLink(Base):
    __tablename__ = "memory_entity_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    # Relationships
    memory: Mapped[Memory] = relationship(back_populates="entity_links")
    entity: Mapped[Entity] = relationship(back_populates="memory_links")

    __table_args__ = (
        UniqueConstraint("memory_id", "entity_id", name="uq_memory_entity_link"),
        Index("idx_mel_memory_id", "memory_id"),
        Index("idx_mel_entity_id", "entity_id"),
    )


# ── Conversations ──


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE")
    )
    raw_content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    project: Mapped[Project | None] = relationship(back_populates="conversations")

    __table_args__ = (
        Index("idx_conversations_project_id", "project_id"),
        Index("idx_conversations_processed", "processed"),
    )
