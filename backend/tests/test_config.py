import pytest
from pydantic import ValidationError

from app.core.config import Settings

# _env_file=None so these don't pick up the developer's real backend/.env.
PROD_OK = {
    "environment": "production",
    "session_secret": "a-real-secret",
    "s3_access_key": "prod-key",
    "s3_secret_key": "prod-secret",
    "google_api_key": "prod-google-key",
}


def test_local_allows_insecure_defaults() -> None:
    settings = Settings(_env_file=None, environment="local")  # defaults intact
    assert settings.session_secret == "change-me"  # no exception


def test_production_rejects_default_session_secret() -> None:
    bad = {**PROD_OK, "session_secret": "change-me"}
    with pytest.raises(ValidationError, match="session_secret"):
        Settings(_env_file=None, **bad)


def test_production_rejects_default_minio_credentials() -> None:
    bad = {**PROD_OK, "s3_access_key": "minioadmin", "s3_secret_key": "minioadmin"}
    with pytest.raises(ValidationError, match="s3_access_key"):
        Settings(_env_file=None, **bad)


def test_production_requires_google_api_key() -> None:
    bad = {**PROD_OK, "google_api_key": ""}
    with pytest.raises(ValidationError, match="google_api_key"):
        Settings(_env_file=None, **bad)


def test_production_accepts_fully_configured_settings() -> None:
    settings = Settings(_env_file=None, **PROD_OK)
    assert settings.environment == "production"
    assert settings.cookie_secure is True
