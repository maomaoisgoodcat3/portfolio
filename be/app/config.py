from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "be/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Portfolio API"
    app_env: str = "development"

    raw_database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

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


settings = Settings()
