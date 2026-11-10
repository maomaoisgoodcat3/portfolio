import re
import secrets
from datetime import datetime, timezone
from typing import Annotated

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_utils import (
    decrypt_totp_secret,
    hash_password,
    verify_password,
    verify_recovery_code,
    verify_totp_code,
)
from app.config import settings
from app.deps import get_db, require_admin
from app.models import AdminSession, AdminUser, LoginEvent, RecoveryCode
from app.rate_limit import clear, is_locked, record_failure
from app.sessions import (
    ABSOLUTE_TTL,
    create_pending_session,
    get_session,
    promote_session,
    purge_expired,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
COOKIE_NAME = "__Host-session"
INVALID_CREDENTIALS = "Invalid credentials"
TOO_MANY_ATTEMPTS = "Too many attempts. Try again later."
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=1024)


class TotpRequest(BaseModel):
    code: str = Field(max_length=32)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _set_session_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_CREDENTIALS,
    )


def _locked(db: Session, email: str, ip: str, now: datetime) -> bool:
    return is_locked(db, f"login:email:{email}", now) or is_locked(
        db, f"login:ip:{ip}", now
    )


def _record_totp_failure(
    db: Session,
    admin: AdminUser,
    email: str,
    ip: str,
    user_agent: str | None,
    now: datetime,
) -> None:
    record_failure(db, f"login:email:{email}", now)
    record_failure(db, f"login:ip:{ip}", now)
    db.add(
        LoginEvent(
            admin_user_id=admin.id,
            email_attempted=email,
            event="totp_fail",
            ip=ip,
            user_agent=user_agent,
            created_at=now,
        )
    )
    db.flush()


@router.post("/login")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, bool]:
    now = datetime.now(timezone.utc)
    email = payload.email.strip().lower()
    ip = _client_ip(request)
    email_key = f"login:email:{email}"
    ip_key = f"login:ip:{ip}"
    if is_locked(db, email_key, now) or is_locked(db, ip_key, now):
        raise HTTPException(status_code=429, detail=TOO_MANY_ATTEMPTS)

    admin = db.scalar(select(AdminUser).where(AdminUser.email == email))
    password_hash = admin.password_hash if admin else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(payload.password, password_hash)
    if admin is None or not password_ok:
        record_failure(db, email_key, now)
        record_failure(db, ip_key, now)
        db.add(
            LoginEvent(
                admin_user_id=admin.id if admin else None,
                email_attempted=email,
                event="password_fail",
                ip=ip,
                user_agent=request.headers.get("user-agent"),
                created_at=now,
            )
        )
        db.commit()
        raise _invalid_credentials()

    purge_expired(db, now)
    token = create_pending_session(
        db,
        admin,
        ip,
        request.headers.get("user-agent"),
        now,
    )
    db.add(
        LoginEvent(
            admin_user_id=admin.id,
            email_attempted=email,
            event="password_ok",
            ip=ip,
            user_agent=request.headers.get("user-agent"),
            created_at=now,
        )
    )
    db.commit()
    _set_session_cookie(response, token, 300)
    return {"mfa_required": True}


@router.post("/totp")
def verify_totp(
    request: Request,
    payload: TotpRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    ip = _client_ip(request)
    raw_token = request.cookies.get(COOKIE_NAME)
    pending = get_session(db, raw_token, require_mfa=False, now=now) if raw_token else None
    if pending is None or pending.mfa_passed:
        raise _invalid_credentials()

    admin = db.get(AdminUser, pending.admin_user_id, with_for_update=True)
    email = admin.email
    if _locked(db, email, ip, now):
        raise HTTPException(status_code=429, detail=TOO_MANY_ATTEMPTS)

    user_agent = request.headers.get("user-agent")
    event = "totp_ok"
    success = False
    if re.fullmatch(r"[0-9]{6}", payload.code):
        try:
            secret = decrypt_totp_secret(admin.totp_secret_enc, settings.totp_enc_key)
        except InvalidToken:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error",
            ) from None
        step = verify_totp_code(secret, payload.code, admin.totp_last_step)
        if step is not None:
            admin.totp_last_step = step
            db.flush()
            success = True
    else:
        recovery_codes = db.scalars(
            select(RecoveryCode).where(
                RecoveryCode.admin_user_id == admin.id,
                RecoveryCode.used_at.is_(None),
            )
        ).all()
        for recovery_code in recovery_codes:
            if verify_recovery_code(payload.code, recovery_code.code_hash):
                recovery_code.used_at = now
                db.flush()
                event = "recovery_used"
                success = True
                break

    if not success:
        _record_totp_failure(db, admin, email, ip, user_agent, now)
        db.commit()
        raise _invalid_credentials()

    new_token, csrf_token = promote_session(db, pending, ip, user_agent, now)
    clear(db, f"login:email:{email}")
    clear(db, f"login:ip:{ip}")
    db.add(
        LoginEvent(
            admin_user_id=admin.id,
            email_attempted=email,
            event=event,
            ip=ip,
            user_agent=user_agent,
            created_at=now,
        )
    )
    db.commit()
    _set_session_cookie(response, new_token, int(ABSOLUTE_TTL.total_seconds()))
    return {"csrf_token": csrf_token}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    session: Annotated[AdminSession, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    db.delete(session)
    db.commit()
    response.delete_cookie(
        COOKIE_NAME,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


@router.get("/me")
def me(
    session: Annotated[AdminSession, Depends(require_admin)],
) -> dict[str, str]:
    return {"email": session.admin_user.email, "csrf_token": session.csrf_token}
