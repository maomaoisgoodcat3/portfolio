from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RateLimitEntry

WINDOW = timedelta(minutes=15)
MAX_FAILURES = 5


def _get_now(now: datetime | None) -> datetime:
    if now is not None and now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now or datetime.now(timezone.utc)


def is_locked(
    db: Session,
    key: str,
    now: datetime | None = None,
) -> bool:
    current = _get_now(now)
    entry = db.scalar(
        select(RateLimitEntry)
        .where(RateLimitEntry.key == key)
        .with_for_update()
    )
    return bool(
        entry is not None
        and current - entry.window_start < WINDOW
        and entry.count >= MAX_FAILURES
    )


def record_failure(
    db: Session,
    key: str,
    now: datetime | None = None,
) -> None:
    current = _get_now(now)
    entry = db.scalar(
        select(RateLimitEntry)
        .where(RateLimitEntry.key == key)
        .with_for_update()
    )
    if entry is None:
        db.add(RateLimitEntry(key=key, window_start=current, count=1))
    elif current - entry.window_start >= WINDOW:
        entry.window_start = current
        entry.count = 1
    else:
        entry.count += 1
    db.flush()


def clear(db: Session, key: str) -> None:
    entry = db.get(RateLimitEntry, key)
    if entry is not None:
        db.delete(entry)
    db.flush()
