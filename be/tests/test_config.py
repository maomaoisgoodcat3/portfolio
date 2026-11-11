import pytest
from pydantic import SecretStr, ValidationError

from app.config import Settings

FERNET_KEY = "0" * 43 + "="


def settings_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "_env_file": None,
        "DATABASE_URL": None,
        "TOTP_ENC_KEY": FERNET_KEY,
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_DB": "database",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": 5432,
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_neon_database_url_is_normalized_and_keeps_query(scheme: str) -> None:
    config = Settings(
        **settings_kwargs(
            DATABASE_URL=SecretStr(
                f"{scheme}://user:password@localhost:5432/database"
                "?sslmode=require&channel_binding=require"
            )
        )
    )

    url = config.get_database_url()

    assert str(url).startswith("postgresql+psycopg://")
    assert url.query["sslmode"] == "require"
    assert url.query["channel_binding"] == "require"


def test_blank_database_url_uses_postgres_settings() -> None:
    config = Settings(**settings_kwargs(DATABASE_URL="   "))

    assert config.database_url is None
    assert config.get_database_url().drivername == "postgresql+psycopg"
    assert config.get_database_url().database == "database"


def test_missing_postgres_settings_error_does_not_contain_password() -> None:
    password = "do-not-leak-this-password"

    with pytest.raises(ValidationError) as error:
        Settings(
            _env_file=None,
            DATABASE_URL=None,
            TOTP_ENC_KEY=FERNET_KEY,
            POSTGRES_PASSWORD=password,
            POSTGRES_USER=None,
            POSTGRES_DB=None,
            POSTGRES_HOST=None,
            POSTGRES_PORT=None,
        )

    assert password not in str(error.value)
