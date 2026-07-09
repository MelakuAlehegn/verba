from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Convenient-but-insecure defaults that must be overridden before production.
_INSECURE_DEFAULTS = {
    "session_secret": "change-me",
    "s3_access_key": "minioadmin",
    "s3_secret_key": "minioadmin",
}

# Anchor .env to backend/ (this file is backend/app/core/config.py) so it loads
# regardless of the process's working directory — uvicorn, celery, alembic, or
# tests can all be launched from anywhere.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
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
    qdrant_collection: str = "document_chunks"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "documents"
    s3_region: str = "us-east-1"
    upload_allowed_extensions: str = ".pdf,.txt,.md,.docx"
    upload_max_bytes: int = 25 * 1024 * 1024  # 25 MB
    chunk_max_tokens: int = 512
    chunk_overlap_tokens: int = 64
    retrieval_top_k: int = 8
    # Minimum cosine similarity for a chunk to count as relevant context. Below
    # this, an off-topic question gets empty context → a grounded "I don't know".
    retrieval_score_threshold: float = 0.5
    # MMR reranking: over-fetch this many candidates, then pick retrieval_top_k by
    # Maximal Marginal Relevance. Set <= retrieval_top_k to disable reranking.
    rerank_candidate_pool: int = 20
    # MMR relevance/diversity balance: 1.0 = pure relevance, 0.0 = pure diversity.
    mmr_lambda: float = 0.7
    # Hybrid search: blend keyword (Postgres full-text) with vector retrieval via
    # RRF, so exact terms/IDs that embeddings miss still surface.
    hybrid_search_enabled: bool = True
    # Query rewriting: fold recent conversation into follow-up questions so they
    # retrieve/generate as standalone queries. Costs one LLM call per follow-up
    # (skipped on the first turn). Set False to disable.
    query_rewrite_enabled: bool = True
    query_rewrite_history_messages: int = 6
    # Conversation memory: include recent turns in the answer prompt so the model
    # keeps continuity across a chat (answers still come only from the sources).
    conversation_memory_enabled: bool = True
    generation_model: str = "gemini-2.5-flash"
    google_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    embedding_version: str = "v1"
    embedding_dimension: int = 768
    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = "change-me"
    session_ttl_days: int = 30
    # Rate limiting: fixed-window per client IP, shared via Redis. Fail-open.
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def upload_allowed_extension_set(self) -> set[str]:
        return {
            ext.strip().lower()
            for ext in self.upload_allowed_extensions.split(",")
            if ext.strip()
        }

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _reject_insecure_production_config(self) -> "Settings":
        """Fail fast at startup if production is left with dev defaults/secrets.

        Local and test keep their convenient defaults; only ``production`` is
        held to the bar, so a misconfigured deploy crashes loudly instead of
        silently shipping with ``change-me`` or ``minioadmin`` credentials.
        """
        if self.environment != "production":
            return self
        problems = [
            f"{field} is still the insecure default"
            for field, insecure in _INSECURE_DEFAULTS.items()
            if getattr(self, field) == insecure
        ]
        if not self.google_api_key:
            problems.append("google_api_key is not set")
        if not self.session_secret:
            problems.append("session_secret is empty")
        if problems:
            raise ValueError(
                "Insecure configuration for production: " + "; ".join(problems)
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
