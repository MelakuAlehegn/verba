"""Cross-tenant isolation contracts.

These assert the *seams* that keep one user out of another's data, without a
live DB: ownership dependencies 404 on someone else's resource (hiding its
existence), services always scope lookups to the caller, and vector search
can't be called without a tenant filter. Row-level SQL scoping (the WHERE
user_id clauses in crud) is enforced in Postgres; verifying that end-to-end
needs a Postgres-backed test DB — a separate harness (see build-state notes).
"""

import inspect
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import chats as chats_ep
from app.api.v1.endpoints import documents as docs_ep
from app.services import chat_service, document_service
from app.services.rag.vector_store import QdrantVectorStore


def _user() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4())


# --- Ownership dependencies: another tenant's resource is a 404, not a 403 ---


def test_get_owned_chat_404_when_not_owned(monkeypatch) -> None:
    # Service returns None for a chat the user doesn't own → indistinguishable
    # from "doesn't exist", so its existence isn't leaked across tenants.
    monkeypatch.setattr(chats_ep, "get_chat_for_user", lambda db, user, chat_id: None)

    with pytest.raises(HTTPException) as exc:
        chats_ep.get_owned_chat(chat_id=uuid4(), db=Mock(), current_user=_user())

    assert exc.value.status_code == 404


def test_get_owned_chat_scopes_lookup_to_current_user(monkeypatch) -> None:
    user = _user()
    captured = {}

    def fake(db, resolved_user, chat_id):
        captured["user"] = resolved_user
        return SimpleNamespace(id=chat_id, user_id=resolved_user.id)

    monkeypatch.setattr(chats_ep, "get_chat_for_user", fake)

    chat = chats_ep.get_owned_chat(chat_id=uuid4(), db=Mock(), current_user=user)

    assert captured["user"] is user  # lookup bound to the caller
    assert chat.user_id == user.id


def test_get_owned_document_404_when_not_owned(monkeypatch) -> None:
    monkeypatch.setattr(docs_ep, "get_document_for_user", lambda db, user, document_id: None)

    with pytest.raises(HTTPException) as exc:
        docs_ep.get_owned_document(document_id=uuid4(), db=Mock(), current_user=_user())

    assert exc.value.status_code == 404


# --- Services always scope crud lookups to the caller's id ---


def test_chat_service_scopes_lookup_to_user(monkeypatch) -> None:
    user = _user()
    captured = {}
    monkeypatch.setattr(
        "app.services.chat_service.get_chat",
        lambda db, chat_id, user_id: captured.update(user_id=user_id),
    )

    chat_service.get_chat_for_user(Mock(), user, uuid4())

    assert captured["user_id"] == user.id


def test_document_service_scopes_lookup_to_user(monkeypatch) -> None:
    user = _user()
    captured = {}
    monkeypatch.setattr(
        "app.services.document_service.get_document",
        lambda db, document_id, user_id: captured.update(user_id=user_id),
    )

    document_service.get_document_for_user(Mock(), user, uuid4())

    assert captured["user_id"] == user.id


# --- Vector search can't be issued without a tenant filter ---


def test_vector_search_requires_user_id() -> None:
    param = inspect.signature(QdrantVectorStore.search).parameters["user_id"]
    # Keyword-only with no default → callers must pass a user_id; there's no way
    # to accidentally run an unscoped search.
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty
