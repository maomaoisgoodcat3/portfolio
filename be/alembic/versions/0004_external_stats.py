"""create external_stats table

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_stats",
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("account", sa.Text(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_attempt_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("provider", "account", name=op.f("pk_external_stats")),
    )


def downgrade() -> None:
    op.drop_table("external_stats")
