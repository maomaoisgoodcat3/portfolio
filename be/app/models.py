import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
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
        Index(
            "uq_blocks_singleton_type",
            "type",
            unique=True,
            postgresql_where=text("type IN ('profile', 'links', 'contact')"),
        ),
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


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    totp_secret_enc: Mapped[str] = mapped_column(Text, nullable=False)
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    totp_last_step: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
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

    recovery_codes: Mapped[list["RecoveryCode"]] = relationship(
        "RecoveryCode",
        back_populates="admin_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sessions: Mapped[list["AdminSession"]] = relationship(
        "AdminSession",
        back_populates="admin_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    login_events: Mapped[list["LoginEvent"]] = relationship(
        "LoginEvent",
        back_populates="admin_user",
    )


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    __table_args__ = (
        Index("ix_recovery_codes_admin_user_id", "admin_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    code_hash: Mapped[str] = mapped_column(Text, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    admin_user: Mapped["AdminUser"] = relationship(
        "AdminUser", back_populates="recovery_codes"
    )


class AdminSession(Base):
    __tablename__ = "sessions"

    __table_args__ = (
        Index("ix_sessions_admin_user_id", "admin_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    csrf_token: Mapped[str] = mapped_column(Text, nullable=False)
    mfa_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    admin_user: Mapped["AdminUser"] = relationship(
        "AdminUser", back_populates="sessions"
    )


class LoginEvent(Base):
    __tablename__ = "login_events"

    __table_args__ = (
        Index("ix_login_events_admin_user_id", "admin_user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    email_attempted: Mapped[str] = mapped_column(Text, nullable=False)
    event: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    admin_user: Mapped["AdminUser | None"] = relationship(
        "AdminUser", back_populates="login_events"
    )


class RateLimitEntry(Base):
    __tablename__ = "rate_limits"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
