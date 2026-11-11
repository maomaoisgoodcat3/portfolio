from __future__ import annotations

import hashlib
import time
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.chat_service import ChatService, DatabaseRetriever
from app.client_ip import get_client_ip
from app.config import Settings
from app.deps import get_db
from app.llm import GeminiClient
from app.models import AppSetting, ChatLog, RateLimitEntry

router = APIRouter(prefix="/api", tags=["chat"])
CHAT_UNAVAILABLE = "Chat is unavailable"
VERIFICATION_UNAVAILABLE = "Verification unavailable"
DAILY_LIMIT_REACHED = "Daily limit reached"


class ChatHistoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=1000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=6)
    turnstile_token: str = Field(min_length=1)


class TurnstileVerifier:
    def verify(self, secret: str, token: str, remoteip: str) -> bool:
        try:
            response = httpx.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={"secret": secret, "response": token, "remoteip": remoteip},
                timeout=5.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=VERIFICATION_UNAVAILABLE,
            ) from None
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=VERIFICATION_UNAVAILABLE,
            )
        return payload.get("success") is True


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _chat_service(request: Request) -> ChatService:
    service = getattr(request.app.state, "chat_service", None)
    if service is None:
        config = _settings(request)
        assert config.gemini_api_key is not None
        assert config.gemini_chat_model is not None
        database_url = config.get_chat_database_url()
        assert database_url is not None
        service = ChatService(
            GeminiClient(
                config.gemini_api_key.get_secret_value(),
                config.gemini_chat_model,
                config.gemini_embed_model,
            ),
            DatabaseRetriever(database_url),
        )
        request.app.state.chat_service = service
    return service


def _ip_hash(config: Settings, client_ip: str) -> str:
    assert config.ip_hash_salt is not None
    return hashlib.sha256(
        config.ip_hash_salt.get_secret_value().encode() + client_ip.encode()
    ).hexdigest()


def _check_ip_limit(db: Session, key: str, now: datetime) -> bool:
    entry = db.scalar(
        select(RateLimitEntry).where(RateLimitEntry.key == key).with_for_update()
    )
    if entry is None:
        db.add(RateLimitEntry(key=key, window_start=now, count=1))
        db.flush()
        return True
    if now - entry.window_start >= timedelta(minutes=10):
        entry.window_start = now
        entry.count = 1
        db.flush()
        return True
    if entry.count >= 5:
        return False
    entry.count += 1
    db.flush()
    return True


def _check_daily_ip_limit(db: Session, key: str, now: datetime) -> bool:
    return _check_window_limit(db, key, now, timedelta(days=1), 30)


def _check_window_limit(
    db: Session,
    key: str,
    now: datetime,
    window: timedelta,
    maximum: int,
) -> bool:
    entry = db.scalar(
        select(RateLimitEntry).where(RateLimitEntry.key == key).with_for_update()
    )
    if entry is None:
        db.add(RateLimitEntry(key=key, window_start=now, count=1))
        db.flush()
        return True
    if now - entry.window_start >= window:
        entry.window_start = now
        entry.count = 1
        db.flush()
        return True
    if entry.count >= maximum:
        return False
    entry.count += 1
    db.flush()
    return True


def _increment_daily_usage(db: Session, current_day: date) -> int:
    result = db.execute(
        text(
            """
            INSERT INTO chat_usage_daily (day, requests)
            VALUES (:day, 1)
            ON CONFLICT (day) DO UPDATE
            SET requests = chat_usage_daily.requests + 1
            RETURNING requests
            """
        ),
        {"day": current_day},
    )
    return int(result.scalar_one())


def _detected_language(question: str) -> str:
    return "vi" if any(char in question for char in "ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặ") else "en"


@router.post("/chat")
def chat(
    payload: ChatRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    config = _settings(request)
    enabled = db.scalar(
        select(AppSetting.value).where(AppSetting.key == "chat_enabled")
    )
    if enabled != "true":
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE)
    if not config.chat_settings_available:
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE)

    client_ip = get_client_ip(request, config)
    ip_hash = _ip_hash(config, client_ip)
    now = datetime.now(timezone.utc)
    if not _check_ip_limit(db, f"chat:{ip_hash}", now) or not _check_daily_ip_limit(
        db, f"chat:daily:{ip_hash}", now
    ):
        db.rollback()
        raise HTTPException(status_code=429, detail="Too many requests")

    verifier = getattr(request.app.state, "turnstile_verifier", TurnstileVerifier())
    assert config.turnstile_secret_key is not None
    if not verifier.verify(
        config.turnstile_secret_key.get_secret_value(),
        payload.turnstile_token,
        client_ip,
    ):
        db.rollback()
        raise HTTPException(status_code=403, detail="Verification failed")

    current_day = date.today()
    usage = _increment_daily_usage(db, current_day)
    if usage > config.chat_daily_limit:
        db.rollback()
        raise HTTPException(status_code=429, detail=DAILY_LIMIT_REACHED)

    started = time.monotonic()
    answer = CHAT_UNAVAILABLE
    sources: list[dict[str, Any]] = []
    refused = True
    error: str | None = None
    try:
        answer, sources, refused, error = _chat_service(request).answer(
            payload.message,
            [item.model_dump() for item in payload.history],
        )
    except Exception as exc:
        error = type(exc).__name__[:80]
    if error is not None and answer == CHAT_UNAVAILABLE:
        answer = CHAT_UNAVAILABLE
        refused = True
    db.add(
        ChatLog(
            ip_hash=ip_hash,
            lang=_detected_language(payload.message),
            question=payload.message[:500],
            answer_chars=len(answer),
            sources=sources,
            latency_ms=int((time.monotonic() - started) * 1000),
            refused=refused,
            error=error,
        )
    )
    db.commit()
    if error is not None:
        raise HTTPException(status_code=503, detail=CHAT_UNAVAILABLE)
    return {"answer": answer, "sources": sources, "refused": refused}
