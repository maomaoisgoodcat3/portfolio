from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "be/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Portfolio API"
    app_env: str = "development"

    postgres_user: str = "portfolio_user"
    postgres_password: str = "portfolio_password"
    postgres_db: str = "portfolio_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432


settings = Settings()
