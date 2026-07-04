from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.endpoints.chats import get_owned_chat
from app.core.deps import get_current_user
from app.main import create_app
from app.services.rag.embedding import get_embedder
from app.services.rag.llm import get_llm_provider
from app.services.rag.vector_store import get_vector_store

CHATS_MODULE = "app.api.v1.endpoints.chats"


def _message(role: str, content: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        chat_id=uuid4(),
        role=role,
        content=content,
        status="complete",
        model=None,
        token_usage=None,
        created_at="2026-01-01T00:00:00Z",
    )


def _override_auth_and_chat(app) -> None:
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_owned_chat] = lambda: SimpleNamespace(id=uuid4(), user_id=uuid4())
    # Never construct real Gemini/Qdrant clients in tests.
    app.dependency_overrides[get_embedder] = lambda: Mock()
    app.dependency_overrides[get_vector_store] = lambda: Mock()
    app.dependency_overrides[get_llm_provider] = lambda: Mock()


def test_list_messages_returns_history(monkeypatch) -> None:
    app = create_app()
    _override_auth_and_chat(app)
    monkeypatch.setattr(
        f"{CHATS_MODULE}.list_messages_for_chat",
        lambda *a, **k: [_message("user", "hi"), _message("assistant", "an answer")],
    )

    client = TestClient(app)
    response = client.get(f"/api/v1/chats/{uuid4()}/messages")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_post_message_returns_user_and_assistant(monkeypatch) -> None:
    app = create_app()
    _override_auth_and_chat(app)
    monkeypatch.setattr(
        f"{CHATS_MODULE}.post_message_to_chat",
        lambda db, chat, payload, **kwargs: (
            _message("user", payload.content),
            _message("assistant", "the grounded answer"),
        ),
    )

    client = TestClient(app)
    response = client.post(f"/api/v1/chats/{uuid4()}/messages", json={"content": "hello"})

    assert response.status_code == 201
    body = response.json()
    assert body["user_message"]["content"] == "hello"
    assert body["assistant_message"]["role"] == "assistant"
    assert body["assistant_message"]["content"] == "the grounded answer"


def test_post_empty_message_returns_422() -> None:
    app = create_app()
    _override_auth_and_chat(app)

    client = TestClient(app)
    response = client.post(f"/api/v1/chats/{uuid4()}/messages", json={"content": ""})

    assert response.status_code == 422


def test_stream_message_emits_token_and_done_events(monkeypatch) -> None:
    app = create_app()
    _override_auth_and_chat(app)
    assistant = _message("assistant", "")
    monkeypatch.setattr(f"{CHATS_MODULE}.recent_history", lambda db, chat_id: [])
    monkeypatch.setattr(f"{CHATS_MODULE}.resolve_chat_scope", lambda db, chat: None)
    monkeypatch.setattr(
        f"{CHATS_MODULE}.start_message_turn",
        lambda db, chat, content: (_message("user", content), assistant),
    )
    monkeypatch.setattr(
        f"{CHATS_MODULE}.stream_message_reply",
        lambda *a, **k: iter(["alpha", "beta"]),
    )

    client = TestClient(app)
    response = client.post(f"/api/v1/chats/{uuid4()}/messages/stream", json={"content": "hi"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert 'data: {"delta": "alpha"}' in body
    assert 'data: {"delta": "beta"}' in body
    assert "event: done" in body
    assert str(assistant.id) in body
