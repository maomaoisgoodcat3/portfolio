import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth_utils import hash_token
from app.models import AdminSession, AdminUser

PENDING_TTL = timedelta(minutes=5)
IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TTL = timedelta(hours=8)


def _get_now(now: datetime | None) -> datetime:
    if now is not None and now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now or datetime.now(timezone.utc)


def create_pending_session(
    db: Session,
    admin: AdminUser,
    ip: str | None,
    user_agent: str | None,
    now: datetime | None = None,
) -> str:
    current = _get_now(now)
    raw_token = secrets.token_urlsafe(32)
    db.add(
        AdminSession(
            admin_user=admin,
            token_hash=hash_token(raw_token),
            csrf_token=secrets.token_urlsafe(32),
            mfa_passed=False,
            created_at=current,
            last_seen_at=current,
            expires_at=current + PENDING_TTL,
            ip=ip,
            user_agent=user_agent,
        )
    )
    db.flush()
    return raw_token


def promote_session(
    db: Session,
    pending: AdminSession,
    ip: str | None,
    user_agent: str | None,
    now: datetime | None = None,
) -> tuple[str, str]:
    current = _get_now(now)
    admin_user_id = pending.admin_user_id
    if pending.mfa_passed or pending.expires_at <= current:
        raise ValueError("Pending session is invalid")
    raw_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    db.delete(pending)
    db.flush()
    db.add(
        AdminSession(
            admin_user_id=admin_user_id,
            token_hash=hash_token(raw_token),
            csrf_token=csrf_token,
            mfa_passed=True,
            created_at=current,
            last_seen_at=current,
            expires_at=current + ABSOLUTE_TTL,
            ip=ip,
            user_agent=user_agent,
        )
    )
    db.flush()
    return raw_token, csrf_token


def get_session(
    db: Session,
    raw_token: str,
    require_mfa: bool = True,
    now: datetime | None = None,
) -> AdminSession | None:
    current = _get_now(now)
    session = db.scalar(
        select(AdminSession).where(AdminSession.token_hash == hash_token(raw_token))
    )
    if session is None:
        return None
    if session.expires_at <= current or (
        session.mfa_passed and session.last_seen_at + IDLE_TIMEOUT <= current
    ):
        delete_session(db, session)
        return None
    if require_mfa and not session.mfa_passed:
        return None
    session.last_seen_at = current
    db.flush()
    return session


def delete_session(db: Session, session: AdminSession) -> None:
    db.delete(session)
    db.flush()


def purge_expired(db: Session, now: datetime | None = None) -> None:
    current = _get_now(now)
    db.execute(delete(AdminSession).where(AdminSession.expires_at <= current))
    db.flush()
