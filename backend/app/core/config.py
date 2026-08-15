"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Mizizi"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # Database
    database_url: str = "postgresql+psycopg://mizizi:mizizi@localhost:5432/mizizi"

    # Storage
    storage_backend: str = "local"  # "local" | "s3"
    storage_local_root: str = "./data"
    storage_endpoint: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_bucket: str = "mizizi"
    storage_region: str = "us-east-1"
    storage_public_base_url: str | None = None

    # Email
    # mail_backend: "console" (dev — prints/logs instead of sending) | "smtp"
    mail_backend: str = "console"
    mail_from: str = "Mizizi <no-reply@mizizi.org>"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()