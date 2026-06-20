from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services.document_service import delete_document_for_user, upload_document_for_user

DOC_SERVICE_MODULE = "app.services.document_service"


def test_upload_stores_bytes_and_creates_queued_row(monkeypatch) -> None:
    db = Mock()
    storage = Mock()
    user = SimpleNamespace(id=uuid4())
    captured = {}

    def fake_create_document(_db, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(f"{DOC_SERVICE_MODULE}.create_document", fake_create_document)

    upload_document_for_user(
        db, user, storage, filename="taxes.pdf", content_type="application/pdf", data=b"hello"
    )

    # Row is created queued, owned by the user, with a deterministic key + checksum.
    assert captured["status"] == "queued"
    assert captured["user_id"] == user.id
    assert captured["size_bytes"] == 5
    assert (
        captured["storage_key"]
        == f"users/{user.id}/documents/{captured['document_id']}/taxes.pdf"
    )
    assert len(captured["checksum"]) == 64  # sha256 hex
    # Bytes pushed to storage under the same key, then committed.
    storage.put_object.assert_called_once_with(captured["storage_key"], b"hello", "application/pdf")
    db.commit.assert_called_once()


def test_delete_removes_object_then_soft_deletes(monkeypatch) -> None:
    db = Mock()
    storage = Mock()
    document = SimpleNamespace(storage_key="users/u/documents/d/taxes.pdf")
    monkeypatch.setattr(f"{DOC_SERVICE_MODULE}.soft_delete_document", lambda *a, **k: document)

    delete_document_for_user(db, document, storage)

    storage.delete_object.assert_called_once_with("users/u/documents/d/taxes.pdf")
    db.commit.assert_called_once()
