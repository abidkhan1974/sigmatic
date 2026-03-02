"""Sigmatic server configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://sigmatic:sigmatic@localhost:5432/sigmatic"
    database_url_sync: str = "postgresql://sigmatic:sigmatic@localhost:5432/sigmatic"
    redis_url: str = "redis://localhost:6379/0"
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
