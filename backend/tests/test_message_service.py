from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.schemas.message import MessageCreate
from app.services.message_service import STUB_MODEL, post_message_to_chat

MESSAGE_SERVICE_MODULE = "app.services.message_service"


def test_post_message_persists_user_and_assistant_turns(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    created = []

    def fake_create_message(_db, **kwargs):
        created.append(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(f"{MESSAGE_SERVICE_MODULE}.create_message", fake_create_message)
    monkeypatch.setattr(f"{MESSAGE_SERVICE_MODULE}.touch_chat", lambda *a, **k: chat)

    user_message, assistant_message = post_message_to_chat(
        db, chat, MessageCreate(content="hello")
    )

    # Two messages persisted, both tenant-tagged with the chat owner.
    assert [m["role"] for m in created] == ["user", "assistant"]
    assert all(m["user_id"] == chat.user_id for m in created)
    assert user_message.content == "hello"
    assert assistant_message.role == "assistant"
    assert assistant_message.model == STUB_MODEL
    assert "hello" in assistant_message.content
    db.commit.assert_called_once()
