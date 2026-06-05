from types import SimpleNamespace
from unittest.mock import Mock

from app.schemas.settings import SettingsUpdate
from app.services.settings_service import (
    get_or_create_user_settings_for_user,
    update_user_settings_for_user,
)


def test_get_or_create_user_settings_for_user_creates_defaults(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id="user-id")
    settings = SimpleNamespace(default_provider="groq", theme="system", retrieval_settings={}, preferences={})

    monkeypatch.setattr("app.services.settings_service.get_user_settings", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.services.settings_service.create_user_settings", lambda *args, **kwargs: settings)

    result = get_or_create_user_settings_for_user(db, user)

    assert result is settings
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(settings)


def test_update_user_settings_for_user_applies_payload(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id="user-id")
    settings = SimpleNamespace(default_provider="groq", theme="system", retrieval_settings={}, preferences={})
    payload = SettingsUpdate(theme="dark")

    monkeypatch.setattr("app.services.settings_service.get_user_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("app.services.settings_service.create_user_settings", lambda *args, **kwargs: settings)
    monkeypatch.setattr("app.services.settings_service.update_user_settings", lambda *args, **kwargs: settings)

    result = update_user_settings_for_user(db, user, payload)

    assert result is settings
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(settings)

