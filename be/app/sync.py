import argparse
import json
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from app.adapters.registry import get_adapters
from app.db_url import normalize_database_url

UPSERT_SUCCESS = text(
    """
    INSERT INTO external_stats
        (provider, account, data, fetched_at, last_attempt_at, last_error)
    VALUES
        (:provider, :account, CAST(:data AS jsonb), :fetched_at, :last_attempt_at, NULL)
    ON CONFLICT (provider, account) DO UPDATE SET
        data = EXCLUDED.data,
        fetched_at = EXCLUDED.fetched_at,
        last_attempt_at = EXCLUDED.last_attempt_at,
        last_error = NULL
    """
)
UPSERT_FAILURE = text(
    """
    INSERT INTO external_stats
        (provider, account, last_attempt_at, last_error)
    VALUES
        (:provider, :account, :last_attempt_at, :last_error)
    ON CONFLICT (provider, account) DO UPDATE SET
        last_attempt_at = EXCLUDED.last_attempt_at,
        last_error = EXCLUDED.last_error
    """
)


def _accounts() -> list[str]:
    return [
        account.strip()
        for account in os.getenv("STATS_GITHUB_ACCOUNTS", "").split(",")
        if account.strip()
    ]


def _short_error(error: Exception) -> str:
    return "GitHub stats fetch failed"


def sync_accounts(database_url: str, accounts: list[str], token: str | None) -> bool:
    engine = create_engine(
        normalize_database_url(database_url),
        poolclass=NullPool,
        hide_parameters=True,
    )
    failed = False
    adapters = get_adapters(token)
    for account in accounts:
        attempted_at = datetime.now(timezone.utc)
        try:
            data = adapters["github"].fetch(account)
            with engine.begin() as connection:
                connection.execute(
                    UPSERT_SUCCESS,
                    {
                        "provider": "github",
                        "account": account,
                        "data": json.dumps(data),
                        "fetched_at": attempted_at,
                        "last_attempt_at": attempted_at,
                    },
                )
        except Exception as error:
            failed = True
            with engine.begin() as connection:
                connection.execute(
                    UPSERT_FAILURE,
                    {
                        "provider": "github",
                        "account": account,
                        "last_attempt_at": attempted_at,
                        "last_error": _short_error(error),
                    },
                )
    engine.dispose()
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.sync")
    args = parser.parse_args()
    del args

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 1
    failed = sync_accounts(database_url, _accounts(), os.getenv("GITHUB_TOKEN"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
