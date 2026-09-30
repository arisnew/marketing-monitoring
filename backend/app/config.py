from __future__ import annotations
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Marketing Monitoring"
    debug: bool = False
    # Set DEBUG=true for Vite dev server CORS (localhost:5173)
    database_url: str = "sqlite:///./data/app.db"
    secret_key: str = "change-me-in-production"
    master_key: str = "change-me-32-byte-fernet-key-base64=="
    access_token_expire_minutes: int = 60 * 24
    scheduler_enabled: bool = True
    scheduler_tick_seconds: int = 60
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    default_notify_webhook_url: str | None = None
    meta_app_id: str | None = None
    meta_app_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
