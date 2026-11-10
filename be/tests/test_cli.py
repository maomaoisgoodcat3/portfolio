"""Integration tests for be/app/cli.py create-admin command.

Tests call the internal create_admin() function directly with the test DB
session so they never spawn a subprocess and always use portfolio_test.
"""

import pyotp
import pytest
from sqlalchemy.orm import Session

from app.cli import create_admin
from app.models import AdminUser, RecoveryCode

_FIXED_TOTP_SECRET = "JBSWY3DPEHPK3PXP"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_getpass(responses: list[str]):
    """Return a getpass stub that pops responses in order."""
    responses = list(responses)

    def _stub(prompt: str = "") -> str:
        return responses.pop(0)

    return _stub


def _make_input(responses: list[str]):
    """Return an input stub that pops responses in order."""
    responses = list(responses)

    def _stub(prompt: str = "") -> str:
        return responses.pop(0)

    return _stub


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_admin_success(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    password = "super-secure-password-123"
    monkeypatch.setattr("getpass.getpass", _make_getpass([password, password]))
    monkeypatch.setattr("app.cli.generate_totp_secret", lambda: _FIXED_TOTP_SECRET)
    monkeypatch.setattr("builtins.input", _make_input([pyotp.TOTP(_FIXED_TOTP_SECRET).now()]))

    create_admin("Admin@Example.COM", db_session)

    # DB state
    users = db_session.query(AdminUser).all()
    assert len(users) == 1
    user = users[0]
    assert user.email == "admin@example.com"  # lowercased
    assert user.totp_enabled is True
    assert user.totp_last_step is not None

    codes = db_session.query(RecoveryCode).filter_by(admin_user_id=user.id).all()
    assert len(codes) == 10
    for code in codes:
        assert code.used_at is None

    # Printed output contains setup info but NOT the password
    captured = capsys.readouterr()
    assert "TOTP setup key" in captured.out
    assert "otpauth URI" in captured.out
    assert "Recovery codes" in captured.out
    assert password not in captured.out


def test_create_admin_refuses_if_admin_exists(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    password = "super-secure-password-123"
    monkeypatch.setattr("getpass.getpass", _make_getpass([password, password]))
    monkeypatch.setattr("app.cli.generate_totp_secret", lambda: _FIXED_TOTP_SECRET)
    monkeypatch.setattr("builtins.input", _make_input([pyotp.TOTP(_FIXED_TOTP_SECRET).now()]))
    create_admin("first@example.com", db_session)

    # Second call must fail
    monkeypatch.setattr("getpass.getpass", _make_getpass([password, password]))
    monkeypatch.setattr("app.cli.generate_totp_secret", lambda: _FIXED_TOTP_SECRET)
    monkeypatch.setattr("builtins.input", _make_input([pyotp.TOTP(_FIXED_TOTP_SECRET).now()]))
    with pytest.raises(SystemExit) as exc_info:
        create_admin("second@example.com", db_session)
    assert exc_info.value.code == 1

    # Still only one admin in the DB
    assert db_session.query(AdminUser).count() == 1


def test_create_admin_rejects_short_password(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    good_password = "long-enough-password-456"
    # First attempt: short password → reject; second attempt: valid
    monkeypatch.setattr(
        "getpass.getpass",
        _make_getpass(["short", good_password, good_password]),
    )
    monkeypatch.setattr("app.cli.generate_totp_secret", lambda: _FIXED_TOTP_SECRET)
    monkeypatch.setattr("builtins.input", _make_input([pyotp.TOTP(_FIXED_TOTP_SECRET).now()]))

    create_admin("admin@example.com", db_session)

    captured = capsys.readouterr()
    assert "at least 12 characters" in captured.out
    assert db_session.query(AdminUser).count() == 1


def test_create_admin_password_mismatch_reprompts(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    good_password = "long-enough-password-789"
    # First attempt: mismatch → reprompt; second attempt: match
    monkeypatch.setattr(
        "getpass.getpass",
        _make_getpass([good_password, "different-password-xyz", good_password, good_password]),
    )
    monkeypatch.setattr("app.cli.generate_totp_secret", lambda: _FIXED_TOTP_SECRET)
    monkeypatch.setattr("builtins.input", _make_input([pyotp.TOTP(_FIXED_TOTP_SECRET).now()]))

    create_admin("admin@example.com", db_session)

    captured = capsys.readouterr()
    assert "do not match" in captured.out
    assert db_session.query(AdminUser).count() == 1


def test_create_admin_three_wrong_codes_fails(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    password = "super-secure-password-123"
    monkeypatch.setattr("getpass.getpass", _make_getpass([password, password]))
    monkeypatch.setattr("app.cli.generate_totp_secret", lambda: _FIXED_TOTP_SECRET)
    monkeypatch.setattr("builtins.input", _make_input(["000000", "111111", "222222"]))

    with pytest.raises(SystemExit) as exc_info:
        create_admin("admin@example.com", db_session)
    assert exc_info.value.code == 1

    assert db_session.query(AdminUser).count() == 0
    assert db_session.query(RecoveryCode).count() == 0


def test_create_admin_invalid_email(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        create_admin("notanemail", db_session)
    assert exc_info.value.code == 1

    assert db_session.query(AdminUser).count() == 0
