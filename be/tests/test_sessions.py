from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.auth_utils import hash_token
from app.models import AdminSession, AdminUser
from app.sessions import (
    ABSOLUTE_TTL,
    IDLE_TIMEOUT,
    create_pending_session,
    get_session,
    promote_session,
    purge_expired,
)


def make_admin(db_session) -> AdminUser:
    admin = AdminUser(
        email="admin@example.com",
        password_hash="hash",
        totp_secret_enc="secret",
    )
    db_session.add(admin)
    db_session.flush()
    return admin


def test_create_pending_session_stores_hash_not_raw_token(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    token = create_pending_session(db_session, make_admin(db_session), "127.0.0.1", "test", now)
    session = db_session.scalar(select(AdminSession))
    assert session.token_hash == hash_token(token)
    assert session.token_hash != token
    assert session.created_at == now
    assert session.last_seen_at == now


def test_promote_session_returns_new_token_and_removes_pending(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    pending_token = create_pending_session(
        db_session, make_admin(db_session), "127.0.0.1", "test", now
    )
    pending = db_session.scalar(select(AdminSession))
    raw_token, csrf_token = promote_session(db_session, pending, "127.0.0.2", "new", now)
    db_session.flush()
    promoted = db_session.scalar(select(AdminSession))
    assert raw_token != pending_token
    assert csrf_token != pending.csrf_token
    assert promoted.token_hash == hash_token(raw_token)
    assert promoted.mfa_passed
    assert promoted.created_at == now
    assert promoted.last_seen_at == now
    assert get_session(db_session, pending_token, require_mfa=False, now=now) is None


def test_pending_session_rejected_when_mfa_required(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    token = create_pending_session(db_session, make_admin(db_session), None, None, now)
    assert get_session(db_session, token, now=now) is None
    assert get_session(db_session, token, require_mfa=False, now=now) is not None


def test_session_expires_after_absolute_ttl(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    admin = make_admin(db_session)
    create_pending_session(db_session, admin, None, None, now)
    pending = db_session.scalar(select(AdminSession))
    token, _ = promote_session(
        db_session,
        pending,
        None,
        None,
        now,
    )
    db_session.flush()
    assert get_session(db_session, token, now=now + ABSOLUTE_TTL) is None


def test_session_expires_after_idle_timeout(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    admin = make_admin(db_session)
    session = AdminSession(
        admin_user_id=admin.id,
        token_hash=hash_token("token"),
        csrf_token="csrf",
        mfa_passed=True,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(hours=8),
    )
    db_session.add(session)
    db_session.flush()
    assert get_session(db_session, "token", now=now + IDLE_TIMEOUT) is None


def test_unknown_token_returns_none(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert get_session(db_session, "unknown", now=now) is None


def test_purge_expired_removes_only_expired_rows(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    admin = make_admin(db_session)
    db_session.add_all(
        [
            AdminSession(
                admin_user_id=admin.id,
                token_hash=hash_token("expired"),
                csrf_token="expired",
                created_at=now,
                last_seen_at=now,
                expires_at=now - timedelta(seconds=1),
            ),
            AdminSession(
                admin_user_id=admin.id,
                token_hash=hash_token("active"),
                csrf_token="active",
                created_at=now,
                last_seen_at=now,
                expires_at=now + timedelta(seconds=1),
            ),
        ]
    )
    db_session.flush()
    purge_expired(db_session, now)
    db_session.flush()
    assert (
        db_session.scalar(
            select(AdminSession).where(AdminSession.csrf_token == "expired")
        )
        is None
    )
    assert (
        db_session.scalar(
            select(AdminSession).where(AdminSession.csrf_token == "active")
        )
        is not None
    )
