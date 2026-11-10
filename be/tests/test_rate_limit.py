from datetime import datetime, timezone

from sqlalchemy import select

from app.models import RateLimitEntry
from app.rate_limit import MAX_FAILURES, WINDOW, clear, is_locked, record_failure


def test_locks_after_five_failures(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for _ in range(MAX_FAILURES):
        record_failure(db_session, "login:email:x", now)
    db_session.flush()
    assert is_locked(db_session, "login:email:x", now)


def test_window_expiry_restarts_count_at_one(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for _ in range(MAX_FAILURES):
        record_failure(db_session, "login:email:x", now)
    later = now + WINDOW
    record_failure(db_session, "login:email:x", later)
    entry = db_session.scalar(
        select(RateLimitEntry).where(RateLimitEntry.key == "login:email:x")
    )
    assert entry.count == 1
    assert entry.window_start == later
    assert not is_locked(db_session, "login:email:x", later)


def test_lock_does_not_cross_keys(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for _ in range(MAX_FAILURES):
        record_failure(db_session, "login:email:x", now)
    db_session.flush()
    assert is_locked(db_session, "login:email:x", now)
    assert not is_locked(db_session, "login:ip:y", now)


def test_clear_removes_lock(db_session):
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for _ in range(MAX_FAILURES):
        record_failure(db_session, "login:email:x", now)
    clear(db_session, "login:email:x")
    db_session.flush()
    assert not is_locked(db_session, "login:email:x", now)
