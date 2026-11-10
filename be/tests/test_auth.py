from datetime import datetime, timedelta, timezone

import pyotp
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth_utils import encrypt_totp_secret, hash_password, hash_recovery_code
from app.config import settings
from app.deps import get_db
from app.main import app
from app.models import AdminSession, AdminUser, Block, RecoveryCode
from app.sessions import create_pending_session

PASSWORD = "correct horse battery staple"
EMAIL = "admin@example.com"
TOTP_SECRET = "JBSWY3DPEHPK3PXP"


@pytest.fixture
def auth_client(db_session) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def admin(db_session) -> AdminUser:
    admin = AdminUser(
        email=EMAIL,
        password_hash=hash_password(PASSWORD),
        totp_secret_enc=encrypt_totp_secret(TOTP_SECRET, settings.totp_enc_key),
    )
    db_session.add(admin)
    db_session.flush()
    return admin


def login(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": EMAIL.upper(), "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.cookies.get("__Host-session")


def complete_totp(client: TestClient) -> tuple[str, str]:
    pending_token = login(client)
    response = client.post(
        "/api/auth/totp",
        json={"code": pyotp.TOTP(TOTP_SECRET).now()},
    )
    assert response.status_code == 200
    return pending_token, response.json()["csrf_token"]


def test_full_login_totp_flow_returns_me(auth_client, admin):
    _, csrf_token = complete_totp(auth_client)
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json() == {"email": EMAIL, "csrf_token": csrf_token}


def test_session_cookie_attributes(auth_client, admin):
    response = auth_client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    cookie = response.headers["set-cookie"]
    assert "__Host-session=" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/" in cookie
    assert "Domain=" not in cookie


def test_totp_replaces_pending_token(auth_client, admin):
    pending_token, _ = complete_totp(auth_client)
    assert auth_client.cookies.get("__Host-session") != pending_token


def test_unknown_email_and_wrong_password_have_same_error(auth_client, admin):
    unknown = auth_client.post(
        "/api/auth/login",
        json={"email": "unknown@example.com", "password": PASSWORD},
    )
    wrong = auth_client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": "wrong"},
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json() == {"detail": "Invalid credentials"}


def test_pending_session_rejected_by_me_and_admin(auth_client, admin):
    login(auth_client)
    assert auth_client.get("/api/auth/me").status_code == 401
    assert auth_client.get("/api/admin/blocks").status_code == 401


def test_wrong_totp_returns_invalid_credentials(auth_client, admin):
    login(auth_client)
    response = auth_client.post("/api/auth/totp", json={"code": "000000"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_reused_totp_step_is_rejected(auth_client, db_session, admin):
    _, _ = complete_totp(auth_client)
    db_session.rollback()
    pending_token = create_pending_session(
        db_session, admin, "testclient", None, datetime.now(timezone.utc)
    )
    db_session.commit()
    auth_client.cookies.set("__Host-session", pending_token)
    response = auth_client.post(
        "/api/auth/totp",
        json={"code": pyotp.TOTP(TOTP_SECRET).now()},
    )
    assert response.status_code == 401


def test_recovery_code_works_once(auth_client, db_session, admin):
    plain_code = "recovery-code"
    db_session.add(
        RecoveryCode(admin_user_id=admin.id, code_hash=hash_recovery_code(plain_code))
    )
    db_session.commit()
    login(auth_client)
    first = auth_client.post("/api/auth/totp", json={"code": plain_code})
    assert first.status_code == 200
    login(auth_client)
    second = auth_client.post("/api/auth/totp", json={"code": plain_code})
    assert second.status_code == 401


def test_sixth_password_attempt_is_rate_limited(auth_client, admin):
    for _ in range(5):
        response = auth_client.post(
            "/api/auth/login",
            json={"email": EMAIL, "password": "wrong"},
        )
        assert response.status_code == 401
    response = auth_client.post(
        "/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many attempts. Try again later."}


def test_admin_patch_requires_csrf_token(auth_client, db_session, admin):
    _, csrf_token = complete_totp(auth_client)
    block = Block(type="about", title="About", position=0)
    db_session.add(block)
    db_session.commit()
    path = f"/api/admin/blocks/{block.id}"
    assert auth_client.patch(path, json={"title": "Changed"}).status_code == 403
    assert (
        auth_client.patch(
            path,
            json={"title": "Changed"},
            headers={"X-CSRF-Token": csrf_token},
        ).status_code
        == 200
    )


def test_logout_deletes_session(auth_client, admin):
    _, csrf_token = complete_totp(auth_client)
    assert (
        auth_client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        ).status_code
        == 204
    )
    assert auth_client.get("/api/auth/me").status_code == 401


def test_expired_session_is_unauthenticated(auth_client, db_session, admin):
    now = datetime.now(timezone.utc)
    token = create_pending_session(db_session, admin, "testclient", None, now)
    session = db_session.scalar(select(AdminSession).where(AdminSession.token_hash.is_not(None)))
    session.mfa_passed = True
    session.expires_at = now - timedelta(seconds=1)
    db_session.commit()
    auth_client.cookies.set("__Host-session", token)
    assert auth_client.get("/api/auth/me").status_code == 401


def test_every_admin_route_requires_authentication(auth_client):
    for route in app.routes:
        if getattr(route, "path", "").startswith("/api/admin"):
            for method in route.methods or set():
                if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    path = route.path.replace("{id}", "00000000-0000-0000-0000-000000000000")
                    path = path.replace(
                        "{block_id}", "00000000-0000-0000-0000-000000000000"
                    )
                    response = auth_client.request(
                        method,
                        path,
                        json={} if method in {"POST", "PUT", "PATCH"} else None,
                    )
                    assert response.status_code == 401
