from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.core.security import hash_password
from app.schemas.auth import OAuthProfile
from app.services.auth_service import (
    authenticate_user,
    register_user_with_password,
    upsert_user_from_oauth_profile,
)

AUTH_SERVICE_MODULE = "app.services.auth_service"


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


def test_register_user_with_password_hashes_and_commits(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id=uuid4())
    captured = {}

    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.get_user_by_email", lambda *a, **k: None)
    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.create_default_user_settings", lambda *a, **k: None)

    def fake_create_user(_db, *, email, name=None, password_hash=None):
        captured.update(email=email, name=name, password_hash=password_hash)
        return user

    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.create_user", fake_create_user)

    result = register_user_with_password(
        db, email="dev@example.com", password="supersecret", name="Dev"
    )

    assert result is user
    # The raw password must never be stored; a bcrypt hash is persisted instead.
    assert captured["password_hash"] != "supersecret"
    assert captured["password_hash"].startswith("$2")
    db.commit.assert_called_once()


def test_register_user_with_password_rejects_taken_email(monkeypatch) -> None:
    db = Mock()
    monkeypatch.setattr(
        f"{AUTH_SERVICE_MODULE}.get_user_by_email", lambda *a, **k: SimpleNamespace(id=uuid4())
    )

    result = register_user_with_password(db, email="taken@example.com", password="supersecret")

    assert result is None
    db.commit.assert_not_called()


def test_authenticate_user_accepts_valid_password(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id=uuid4(), password_hash=hash_password("supersecret"))
    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.get_user_by_email", lambda *a, **k: user)
    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.touch_user_last_login", lambda *a, **k: user)

    result = authenticate_user(db, email="dev@example.com", password="supersecret")

    assert result is user
    db.commit.assert_called_once()


def test_authenticate_user_rejects_wrong_password(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id=uuid4(), password_hash=hash_password("supersecret"))
    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.get_user_by_email", lambda *a, **k: user)

    result = authenticate_user(db, email="dev@example.com", password="wrong")

    assert result is None
    db.commit.assert_not_called()


def test_authenticate_user_rejects_oauth_only_user(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id=uuid4(), password_hash=None)
    monkeypatch.setattr(f"{AUTH_SERVICE_MODULE}.get_user_by_email", lambda *a, **k: user)

    result = authenticate_user(db, email="oauth@example.com", password="whatever")

    assert result is None

