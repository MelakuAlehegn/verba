from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "document-qa-rag-api"
    app_version: str = "0.1.0"
    environment: Literal["local", "staging", "production", "test"] = "local"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:8080"
    frontend_url: str = "http://localhost:8080"
    google_auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"
    google_redirect_uri: str = "http://127.0.0.1:8000/api/v1/auth/google/callback"
    google_scope: str = "openid email profile"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/document_qa_rag"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = "change-me"
    session_ttl_days: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
