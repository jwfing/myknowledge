"""Convert all datetime columns from TIMESTAMP to TIMESTAMPTZ.

Revision ID: 0002
Create Date: 2026-02-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

# All (table, column) pairs that need conversion
_COLUMNS = [
    ("projects", "created_at"),
    ("projects", "updated_at"),
    ("memories", "created_at"),
    ("memories", "updated_at"),
    ("entities", "created_at"),
    ("entities", "updated_at"),
    ("relations", "created_at"),
    ("memory_entity_links", "created_at"),
    ("conversations", "created_at"),
    ("conversations", "processed_at"),
]


def upgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=False),
        )