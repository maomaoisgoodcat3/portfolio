import hmac
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import AdminSession
from app.sessions import get_session


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AdminSession:
    raw_token = request.cookies.get("__Host-session")
    session = get_session(db, raw_token) if raw_token else None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token or not hmac.compare_digest(
            csrf_token.encode(), session.csrf_token.encode()
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF check failed",
            )
    db.commit()
    return session
