"""Unit tests for be/app/auth_utils.py.

No database, no network, no environment variables are required.
The Fernet key is generated fresh for each test module load.
"""

from cryptography.fernet import Fernet

from app.auth_utils import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_recovery_codes,
    generate_totp_secret,
    hash_password,
    hash_recovery_code,
    hash_token,
    make_totp_uri,
    verify_password,
    verify_recovery_code,
    verify_totp_code,
)

# A fresh Fernet key used only within this test module — never read from env.
_TEST_FERNET_KEY: str = Fernet.generate_key().decode()


# ---------------------------------------------------------------------------
# Argon2 password helpers
# ---------------------------------------------------------------------------


def test_hash_password_returns_argon2_hash() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed.startswith("$argon2")


def test_verify_password_correct() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_verify_password_wrong() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


# ---------------------------------------------------------------------------
# SHA-256 token hash
# ---------------------------------------------------------------------------


def test_hash_token_is_deterministic() -> None:
    token = "some-random-session-token"
    assert hash_token(token) == hash_token(token)
    assert len(hash_token(token)) == 64  # hex SHA-256


# ---------------------------------------------------------------------------
# Fernet / TOTP helpers
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_totp_secret_roundtrip() -> None:
    secret = generate_totp_secret()
    enc = encrypt_totp_secret(secret, _TEST_FERNET_KEY)
    assert enc != secret
    assert decrypt_totp_secret(enc, _TEST_FERNET_KEY) == secret


def test_totp_verify_valid_code() -> None:
    import pyotp

    secret = generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert isinstance(verify_totp_code(secret, code, None), int)


def test_totp_verify_invalid_code() -> None:
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "000000", None) is None


def test_totp_verify_replay_rejected() -> None:
    import pyotp

    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    matched_step = verify_totp_code(secret, code, None)
    assert matched_step is not None
    assert verify_totp_code(secret, code, matched_step) is None


def test_totp_verify_non_ascii_digits_rejected() -> None:
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "١٢٣٤٥٦", None) is None


def test_verify_password_corrupted_hash() -> None:
    assert verify_password("some-password", "not-a-hash") is False


def test_verify_recovery_code_corrupted_hash() -> None:
    assert verify_recovery_code("some-code", "not-a-hash") is False


def test_make_totp_uri_contains_issuer_and_email() -> None:
    secret = generate_totp_secret()
    uri = make_totp_uri(secret, "admin@example.com")
    assert "Portfolio+Admin" in uri or "Portfolio%20Admin" in uri or "Portfolio Admin" in uri
    assert "admin%40example.com" in uri or "admin@example.com" in uri


# ---------------------------------------------------------------------------
# Recovery codes
# ---------------------------------------------------------------------------


def test_generate_recovery_codes_count_and_length() -> None:
    codes = generate_recovery_codes(10)
    assert len(codes) == 10
    for code in codes:
        # secrets.token_urlsafe(16) → 22-char base64url string
        assert len(code) >= 16


def test_hash_and_verify_recovery_code_correct() -> None:
    code = "test-recovery-code-abc123"
    hashed = hash_recovery_code(code)
    assert verify_recovery_code(code, hashed) is True


def test_hash_and_verify_recovery_code_wrong() -> None:
    hashed = hash_recovery_code("correct-code")
    assert verify_recovery_code("wrong-code", hashed) is False
