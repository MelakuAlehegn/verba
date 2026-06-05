from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.schemas.auth import OAuthProfile
from app.services.auth_service import upsert_user_from_oauth_profile


def test_upsert_user_from_oauth_profile_creates_user_when_account_missing(monkeypatch) -> None:
    db = Mock()
    user_id = uuid4()
    user = SimpleNamespace(id=user_id, name=None, avatar_url=None)

    monkeypatch.setattr("app.services.auth_service.get_oauth_account", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.services.auth_service.get_user_by_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "app.services.auth_service.create_user",
        lambda *args, **kwargs: user,
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_default_user_settings",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.auth_service.create_oauth_account",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.auth_service.touch_user_last_login",
        lambda *args, **kwargs: user,
    )

    profile = OAuthProfile(
        provider="google",
        provider_account_id="google-sub-123",
        email="dev@example.com",
        name="Dev",
        avatar_url="https://example.com/avatar.png",
    )

    result = upsert_user_from_oauth_profile(db, profile)

    assert result is user
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)

