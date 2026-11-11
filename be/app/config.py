from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "be/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = "Portfolio API"
    app_env: Literal["development", "production"] = "production"

    totp_enc_key: str = Field(validation_alias="TOTP_ENC_KEY")

    database_url: SecretStr | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )

    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_db: str | None = None
    postgres_host: str | None = None
    postgres_port: int | None = None
    client_ip_header: str = Field(default="", validation_alias="CLIENT_IP_HEADER")

    @field_validator("database_url", mode="before")
    @classmethod
    def _empty_database_url_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _validate_settings(self) -> "Settings":
        if self.database_url is None and any(
            value is None
            for value in (
                self.postgres_user,
                self.postgres_password,
                self.postgres_db,
                self.postgres_host,
                self.postgres_port,
            )
        ):
            raise ValueError(
                "DATABASE_URL is not set; configure POSTGRES_HOST, POSTGRES_PORT, "
                "POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB."
            )

        from cryptography.fernet import Fernet

        try:
            Fernet(self.totp_enc_key.encode())
        except Exception:
            raise ValueError(
                "TOTP_ENC_KEY is not a valid Fernet key. "
                "Generate one with: "
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            ) from None
        return self

    def get_database_url(self) -> URL:
        if self.database_url is not None:
            url = make_url(self.database_url.get_secret_value())
            if url.drivername in {"postgres", "postgresql", "postgresql+psycopg2"}:
                url = url.set(drivername="postgresql+psycopg")
            return url
        assert (
            self.postgres_user is not None
            and self.postgres_password is not None
            and self.postgres_db is not None
            and self.postgres_host is not None
            and self.postgres_port is not None
        )
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
