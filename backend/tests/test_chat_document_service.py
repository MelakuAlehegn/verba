from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services import chat_document_service as svc
from app.services.chat_document_service import (
    UnknownDocumentError,
    resolve_chat_scope,
    set_chat_sources,
)

MODULE = "app.services.chat_document_service"


def test_set_sources_rejects_documents_the_user_does_not_own(monkeypatch) -> None:
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    mine = uuid4()
    monkeypatch.setattr(f"{MODULE}.list_documents", lambda db, uid: [SimpleNamespace(id=mine)])

    with pytest.raises(UnknownDocumentError):
        set_chat_sources(Mock(), chat, [mine, uuid4()])  # second id is not the user's


def test_set_sources_persists_and_returns_resolved(monkeypatch) -> None:
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    mine = uuid4()
    resolved = [SimpleNamespace(id=mine)]
    saved = {}

    monkeypatch.setattr(f"{MODULE}.list_documents", lambda db, uid: [SimpleNamespace(id=mine)])
    monkeypatch.setattr(
        f"{MODULE}.set_chat_documents",
        lambda db, *, chat_id, user_id, document_ids: saved.update(ids=document_ids),
    )
    monkeypatch.setattr(f"{MODULE}.get_scoped_documents", lambda db, cid, uid: resolved)
    db = Mock()

    result = set_chat_sources(db, chat, [mine])

    assert saved["ids"] == [mine]
    assert result == resolved
    db.commit.assert_called_once()


def test_resolve_scope_none_when_no_sources_attached(monkeypatch) -> None:
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    monkeypatch.setattr(f"{MODULE}.list_chat_document_ids", lambda db, cid: [])

    assert resolve_chat_scope(Mock(), chat) is None  # unscoped → all docs


def test_resolve_scope_returns_ready_source_ids(monkeypatch) -> None:
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    live = uuid4()
    monkeypatch.setattr(f"{MODULE}.list_chat_document_ids", lambda db, cid: [live, uuid4()])
    # One attached doc was since deleted, so only the live one resolves.
    monkeypatch.setattr(
        f"{MODULE}.get_scoped_documents", lambda db, cid, uid: [SimpleNamespace(id=live)]
    )

    assert resolve_chat_scope(Mock(), chat) == [live]


def test_module_exposes_list_helper() -> None:
    # sanity: public surface is importable
    assert hasattr(svc, "list_chat_sources")
