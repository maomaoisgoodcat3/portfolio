"""add singleton block type index

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INDEX_NAME = "uq_blocks_singleton_type"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        "blocks",
        ["type"],
        unique=True,
        postgresql_where=sa.text("type IN ('profile', 'links', 'contact')"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="blocks")
