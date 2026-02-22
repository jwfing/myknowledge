"""Shared data models and enums."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ──


class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"


class EntityType(str, Enum):
    PROJECT = "Project"
    API = "API"
    COMPONENT = "Component"
    TECH_STACK = "TechStack"
    CONFIG = "Config"


class RelationType(str, Enum):
    EXPOSES = "exposes"
    DEPENDS_ON = "depends_on"
    USES = "uses"
    CONFIGURED_WITH = "configured_with"


# ── Request Models ──


class ConversationIngestRequest(BaseModel):
    """Request to ingest a raw conversation from Claude Code hook."""

    session_id: str
    project_name: str | None = None
    messages: list[dict[str, Any]]
    metadata: dict[str, Any] | None = None


class RememberRequest(BaseModel):
    """Request to save a knowledge snippet (Hot Path)."""

    content: str
    memory_type: MemoryType
    project_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    importance: float = Field(default=0.8, ge=0, le=1)


class QueryRequest(BaseModel):
    """Request to search memories."""

    query: str
    project_name: str | None = None
    memory_types: list[MemoryType] | None = None
    limit: int = Field(default=3, ge=1, le=5)


# ── Response Models ──


class MemoryResponse(BaseModel):
    id: UUID
    content: str
    memory_type: MemoryType
    importance: float
    project_name: str | None = None
    tags: list[str]
    created_at: datetime
    score: float | None = None


class QueryResponse(BaseModel):
    results: list[MemoryResponse]
    total_found: int
    query_time_ms: float | None = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    tech_stack: list[str]
    memory_count: int
    created_at: datetime


class IngestResponse(BaseModel):
    conversation_id: UUID
    status: str = "queued"
    message: str = "Conversation queued for extraction."


class HealthResponse(BaseModel):
    status: str = "ok"
    database: str = "unknown"
    embedding_model: str = "unknown"


# ── Internal Models (used by extraction pipeline) ──


class ExtractedKnowledge(BaseModel):
    """A single knowledge fragment extracted by the LLM."""

    content: str
    memory_type: MemoryType
    importance: float = Field(default=0.5, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    entities: list[dict[str, str]] = Field(default_factory=list)
    # Each entity: {"name": "OAuth API", "type": "API"}
    relations: list[dict[str, str]] = Field(default_factory=list)
    # Each relation: {"source": "Platform Project", "target": "OAuth API", "type": "exposes"}
