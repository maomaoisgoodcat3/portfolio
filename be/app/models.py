import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Block(Base):
    __tablename__ = "blocks"

    __table_args__ = (
        CheckConstraint(
            "type IN ('profile', 'about', 'skills', 'experience', 'projects', 'research', 'links', 'stats', 'contact')",
            name="type",
        ),
        CheckConstraint("char_length(title) <= 200", name="title_length"),
        CheckConstraint("visibility IN ('public', 'admin')", name="visibility"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    visibility: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="admin",
        server_default="admin",
    )
    props: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list["BlockItem"]] = relationship(
        "BlockItem",
        back_populates="block",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class BlockItem(Base):
    __tablename__ = "block_items"

    __table_args__ = (
        CheckConstraint("visibility IN ('public', 'admin')", name="visibility"),
        Index("ix_block_items_block_id_position", "block_id", "position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    block_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visibility: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="admin",
        server_default="admin",
    )
    data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    block: Mapped["Block"] = relationship("Block", back_populates="items")
