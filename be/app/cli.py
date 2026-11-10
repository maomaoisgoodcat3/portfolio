"""CLI entry point: python -m app.cli <command>

Available commands:
    create-admin --email <addr>   Bootstrap the first admin user.
"""

import argparse
import getpass
import sys

from sqlalchemy.orm import Session

from app.auth_utils import (
    encrypt_totp_secret,
    generate_recovery_codes,
    generate_totp_secret,
    hash_password,
    hash_recovery_code,
    make_totp_uri,
)
from app.config import settings
from app.db import SessionLocal
from app.models import AdminUser, RecoveryCode

# ---------------------------------------------------------------------------
# Core logic (testable without subprocess)
# ---------------------------------------------------------------------------


def create_admin(email: str, db: Session) -> None:
    """Create the first admin user interactively.

    Raises SystemExit with a message on validation failure so callers can
    catch it in tests without spawning a subprocess.
    """
    email = email.strip().lower()
    if not email:
        print("Error: email must not be empty.", file=sys.stderr)
        raise SystemExit(1)

    existing = db.query(AdminUser).first()
    if existing is not None:
        print("Error: an admin user already exists.", file=sys.stderr)
        raise SystemExit(1)

    # Prompt for password (loop until valid + confirmed)
    while True:
        password = getpass.getpass("Password (min 12 chars): ")
        if len(password) < 12:
            print("Password must be at least 12 characters. Try again.")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Try again.")
            continue
        break

    # Generate TOTP + recovery codes
    totp_secret = generate_totp_secret()
    totp_secret_enc = encrypt_totp_secret(totp_secret, settings.totp_enc_key)
    totp_uri = make_totp_uri(totp_secret, email)
    plain_codes = generate_recovery_codes(10)

    # Persist in a single transaction
    admin = AdminUser(
        email=email,
        password_hash=hash_password(password),
        totp_secret_enc=totp_secret_enc,
        totp_enabled=True,
    )
    db.add(admin)
    db.flush()  # get admin.id before inserting codes

    for code in plain_codes:
        db.add(RecoveryCode(admin_user_id=admin.id, code_hash=hash_recovery_code(code)))

    db.commit()

    # Print setup info — never print password or Fernet key
    print(f"\nAdmin user created: {email}")
    print(f"\nTOTP setup key:  {totp_secret}")
    print(f"otpauth URI:     {totp_uri}")
    print("\nRecovery codes (save these now — shown once):")
    for code in plain_codes:
        print(f"  {code}")


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def _cmd_create_admin(args: argparse.Namespace) -> None:
    db = SessionLocal()
    try:
        create_admin(args.email, db)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create-admin", help="Create the first admin user.")
    p_create.add_argument("--email", required=True, help="Admin email address.")

    args = parser.parse_args()

    if args.command == "create-admin":
        _cmd_create_admin(args)
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
