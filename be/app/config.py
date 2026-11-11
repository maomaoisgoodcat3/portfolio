from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


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

    raw_database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    @model_validator(mode="after")
    def _validate_fernet_key(self) -> "Settings":
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

    @property
    def database_url(self) -> URL | str:
        return self.get_database_url()

    def get_database_url(self) -> URL | str:
        if self.raw_database_url:
            return self.raw_database_url
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
