"""create blocks and block_items tables

Revision ID: 0001
Revises:
Create Date: 2026-11-09

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.Text(), server_default="admin", nullable=False),
        sa.Column(
            "props",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type IN ('profile', 'about', 'skills', 'experience', 'projects', 'research', 'links', 'stats', 'contact')",
            name=op.f("ck_blocks_type"),
        ),
        sa.CheckConstraint("char_length(title) <= 200", name=op.f("ck_blocks_title_length")),
        sa.CheckConstraint("visibility IN ('public', 'admin')", name=op.f("ck_blocks_visibility")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blocks")),
    )
    op.create_index(op.f("ix_blocks_position"), "blocks", ["position"], unique=False)

    op.create_table(
        "block_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("block_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.Text(), server_default="admin", nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "visibility IN ('public', 'admin')",
            name=op.f("ck_block_items_visibility"),
        ),
        sa.ForeignKeyConstraint(
            ["block_id"],
            ["blocks.id"],
            name=op.f("fk_block_items_block_id_blocks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_block_items")),
    )
    op.create_index(
        op.f("ix_block_items_block_id_position"),
        "block_items",
        ["block_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_block_items_block_id_position"), table_name="block_items")
    op.drop_table("block_items")
    op.drop_index(op.f("ix_blocks_position"), table_name="blocks")
    op.drop_table("blocks")
