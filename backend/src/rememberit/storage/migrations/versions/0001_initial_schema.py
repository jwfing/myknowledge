"""Initial schema with all 6 tables.

Revision ID: 0001
Create Date: 2026-02-22
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── projects ──
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("tech_stack", ARRAY(sa.Text), server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )

    # ── memories ──
    op.create_table(
        "memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("memory_type", sa.String(20), nullable=False),
        sa.Column("importance", sa.Float, server_default="0.5"),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("tags", ARRAY(sa.Text), server_default="{}"),
        sa.Column("source_session_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
    )
    op.create_index("idx_memories_project_id", "memories", ["project_id"])
    op.create_index("idx_memories_created_at", "memories", ["created_at"])
    op.create_index("idx_memories_tags", "memories", ["tags"], postgresql_using="gin")
    # Note: ivfflat index requires existing data rows; create after seeding
    # or use hnsw which doesn't require pre-existing data
    op.execute(
        "CREATE INDEX idx_memories_embedding ON memories "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    # ── entities ──
    op.create_table(
        "entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("description", sa.Text),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "name", "entity_type", name="uq_entity_project_name_type"),
    )
    op.create_index("idx_entities_project_id", "entities", ["project_id"])
    op.create_index("idx_entities_type", "entities", ["entity_type"])

    # ── relations ──
    op.create_table(
        "relations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("metadata", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.UniqueConstraint("source_entity_id", "target_entity_id", "relation_type", name="uq_relation_src_tgt_type"),
    )
    op.create_index("idx_relations_source", "relations", ["source_entity_id"])
    op.create_index("idx_relations_target", "relations", ["target_entity_id"])

    # ── memory_entity_links ──
    op.create_table(
        "memory_entity_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("memory_id", UUID(as_uuid=True), sa.ForeignKey("memories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.UniqueConstraint("memory_id", "entity_id", name="uq_memory_entity_link"),
    )
    op.create_index("idx_mel_memory_id", "memory_entity_links", ["memory_id"])
    op.create_index("idx_mel_entity_id", "memory_entity_links", ["entity_id"])

    # ── conversations ──
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", sa.String(255), unique=True, nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("raw_content", JSONB, nullable=False),
        sa.Column("processed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime),
    )
    op.create_index("idx_conversations_project_id", "conversations", ["project_id"])
    op.create_index("idx_conversations_processed", "conversations", ["processed"])


def downgrade() -> None:
    op.drop_table("conversations")
    op.drop_table("memory_entity_links")
    op.drop_table("relations")
    op.drop_table("entities")
    op.drop_table("memories")
    op.drop_table("projects")
    op.execute("DROP EXTENSION IF EXISTS vector")
