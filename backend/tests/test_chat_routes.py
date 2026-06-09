from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.endpoints.chats import get_owned_chat
from app.core.deps import get_current_user
from app.main import create_app

CHATS_MODULE = "app.api.v1.endpoints.chats"


def _chat(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        title="New chat",
        provider="groq",
        pinned_at=None,
        archived_at=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_list_and_create_chats(monkeypatch) -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())

    monkeypatch.setattr(f"{CHATS_MODULE}.list_chats_for_user", lambda *a, **k: [_chat()])
    monkeypatch.setattr(
        f"{CHATS_MODULE}.create_chat_for_user",
        lambda db, user, payload: _chat(title=payload.title or "New chat"),
    )

    client = TestClient(app)

    list_response = client.get("/api/v1/chats")
    create_response = client.post("/api/v1/chats", json={"title": "Taxes"})

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Taxes"


def test_get_patch_delete_owned_chat(monkeypatch) -> None:
    app = create_app()
    chat = _chat(title="Renamed")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_owned_chat] = lambda: chat

    monkeypatch.setattr(
        f"{CHATS_MODULE}.update_chat_for_user",
        lambda db, c, payload: _chat(title=payload.title),
    )
    monkeypatch.setattr(f"{CHATS_MODULE}.delete_chat_for_user", lambda *a, **k: None)

    client = TestClient(app)

    get_response = client.get(f"/api/v1/chats/{chat.id}")
    patch_response = client.patch(f"/api/v1/chats/{chat.id}", json={"title": "Renamed"})
    delete_response = client.delete(f"/api/v1/chats/{chat.id}")

    assert get_response.status_code == 200
    assert patch_response.json()["title"] == "Renamed"
    assert delete_response.status_code == 204


def test_get_missing_chat_returns_404(monkeypatch) -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    monkeypatch.setattr(f"{CHATS_MODULE}.get_chat_for_user", lambda *a, **k: None)

    client = TestClient(app)
    response = client.get(f"/api/v1/chats/{uuid4()}")

    assert response.status_code == 404
