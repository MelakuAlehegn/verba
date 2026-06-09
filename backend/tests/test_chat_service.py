from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.schemas.chat import ChatCreate, ChatUpdate
from app.services.chat_service import (
    create_chat_for_user,
    delete_chat_for_user,
    update_chat_for_user,
)

CHAT_SERVICE_MODULE = "app.services.chat_service"


def test_create_chat_for_user_commits_and_refreshes(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id=uuid4())
    chat = SimpleNamespace(id=uuid4())

    captured = {}

    def fake_create_chat(_db, *, user_id, **kwargs):
        captured["user_id"] = user_id
        captured["kwargs"] = kwargs
        return chat

    monkeypatch.setattr(f"{CHAT_SERVICE_MODULE}.create_chat", fake_create_chat)

    result = create_chat_for_user(db, user, ChatCreate(title="Taxes"))

    assert result is chat
    # exclude_none drops the unset provider, so the crud default applies.
    assert captured["user_id"] == user.id
    assert captured["kwargs"] == {"title": "Taxes"}
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(chat)


def test_update_chat_for_user_passes_only_set_fields(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4())
    captured = {}

    def fake_update_chat(_db, _chat, **kwargs):
        captured.update(kwargs)
        return chat

    monkeypatch.setattr(f"{CHAT_SERVICE_MODULE}.update_chat", fake_update_chat)

    result = update_chat_for_user(db, chat, ChatUpdate(title="Renamed"))

    assert result is chat
    assert captured == {"title": "Renamed"}
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(chat)


def test_delete_chat_for_user_commits(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(f"{CHAT_SERVICE_MODULE}.delete_chat", lambda *a, **k: None)

    delete_chat_for_user(db, chat)

    db.commit.assert_called_once()
