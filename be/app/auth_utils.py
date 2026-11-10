"""Auth helpers: Argon2 password hashing, Fernet/TOTP encryption, recovery codes.

Nothing in this module logs passwords, codes, tokens or secrets.
"""

import hashlib
import hmac
import re
import secrets
import time

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
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
    except (VerifyMismatchError, VerificationError, InvalidHashError):
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


def verify_totp_code(secret: str, code: str, last_step: int | None) -> int | None:
    """Verify a TOTP *code* against *secret* with replay protection.

    Checks the previous, current, and next 30-second time steps.
    Returns the matched time step (int) on success, or None on failure.

    Returns None if:
    - *code* is not exactly 6 ASCII digits.
    - No time step matches.
    - The matched step is <= *last_step* (replay detected).

    Pass *last_step=None* when there is no prior step (e.g. first login or CLI).
    """
    if not re.fullmatch(r"[0-9]{6}", code):
        return None

    now_step = int(time.time()) // 30
    totp = pyotp.TOTP(secret)

    for step in (now_step - 1, now_step, now_step + 1):
        expected = totp.at(step * 30)
        if hmac.compare_digest(code, expected):
            if last_step is not None and step <= last_step:
                return None  # replay rejected
            return step

    return None


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
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
