import os
import subprocess
import sys
from datetime import datetime, timezone

from sqlalchemy import text

from app.models import ExternalStats
from app.sync import sync_accounts


def test_sync_help_does_not_require_application_settings() -> None:
    environment = os.environ.copy()
    for name in (
        "TOTP_ENC_KEY",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ):
        environment.pop(name, None)

    result = subprocess.run(
        [sys.executable, "-m", "app.sync", "--help"],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout


def test_sync_failure_keeps_old_data_and_does_not_store_token(
    db_session, monkeypatch
) -> None:
    token = "secret-token"
    db_session.add(
        ExternalStats(
            provider="github",
            account="owner",
            data={"stars": 12},
            fetched_at=None,
            last_attempt_at=datetime.now(timezone.utc),
            last_error=None,
        )
    )
    db_session.commit()

    class FailingAdapter:
        def fetch(self, account: str) -> dict[str, object]:
            raise RuntimeError(f"request failed with {token}")

    monkeypatch.setattr(
        "app.sync.get_adapters",
        lambda value: {"github": FailingAdapter()},
    )
    failed = sync_accounts(
        db_session.get_bind().url.render_as_string(hide_password=False),
        ["owner"],
        token,
    )

    assert failed is True
    row = db_session.execute(
        text(
            "SELECT data, last_error FROM external_stats "
            "WHERE provider = 'github' AND account = 'owner'"
        )
    ).one()
    assert row[0] == {"stars": 12}
    assert token not in row[1]
