"""Auth helpers: Argon2 password hashing, Fernet/TOTP encryption, recovery codes.

Nothing in this module logs passwords, codes, tokens or secrets.
"""

import hashlib
import secrets

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet

_ph = PasswordHasher()


# ---------------------------------------------------------------------------
# Argon2 password helpers
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return an Argon2id hash of *plain*."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*, False otherwise.

    Always runs the full Argon2 verification to avoid timing side-channels.
    """
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


# ---------------------------------------------------------------------------
# SHA-256 token hash (session tokens stored in DB)
# ---------------------------------------------------------------------------


def hash_token(token: str) -> str:
    """Return the hex SHA-256 digest of *token* for safe DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Fernet / TOTP helpers
# ---------------------------------------------------------------------------


def encrypt_totp_secret(secret: str, key: str) -> str:
    """Encrypt a plain TOTP *secret* with the Fernet *key*.

    Returns a URL-safe base64 token (str).
    """
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(secret.encode()).decode()


def decrypt_totp_secret(enc: str, key: str) -> str:
    """Decrypt a Fernet-encrypted TOTP secret back to plain text."""
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.decrypt(enc.encode()).decode()


def generate_totp_secret() -> str:
    """Return a new random base32 TOTP secret."""
    return pyotp.random_base32()


def make_totp_uri(secret: str, email: str) -> str:
    """Return an otpauth:// URI suitable for QR-code / authenticator import."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        email, issuer_name="Portfolio Admin"
    )


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """Return True if *code* is a valid TOTP token for *secret*.

    *valid_window=1* accepts the previous and next 30-second windows.
    """
    return pyotp.TOTP(secret).verify(code, valid_window=valid_window)


# ---------------------------------------------------------------------------
# Recovery codes
# ---------------------------------------------------------------------------


def generate_recovery_codes(n: int = 10) -> list[str]:
    """Return *n* plain-text recovery codes (URL-safe random strings).

    Each code is shown to the admin once; callers must hash and store them.
    """
    return [secrets.token_urlsafe(16) for _ in range(n)]


def hash_recovery_code(code: str) -> str:
    """Return an Argon2id hash of a recovery *code* for safe DB storage."""
    return _ph.hash(code)


def verify_recovery_code(plain: str, hashed: str) -> bool:
    """Return True if plain recovery *code* matches *hashed*, False otherwise."""
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False
