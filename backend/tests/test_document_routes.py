from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.endpoints.documents import get_owned_document
from app.core.deps import get_current_user
from app.main import create_app
from app.storage import get_storage_client

DOCS_MODULE = "app.api.v1.endpoints.documents"


def _document(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        filename="taxes.pdf",
        mime_type="application/pdf",
        size_bytes=5,
        status="queued",
        chunk_count=0,
        error_code=None,
        error_message=None,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _app_with_overrides() -> object:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    # Never touch real MinIO in tests.
    app.dependency_overrides[get_storage_client] = lambda: MagicMock()
    return app


def test_list_documents(monkeypatch) -> None:
    app = _app_with_overrides()
    monkeypatch.setattr(f"{DOCS_MODULE}.list_documents_for_user", lambda *a, **k: [_document()])

    client = TestClient(app)
    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "storage_key" not in response.json()[0]  # internal field stays hidden


def test_upload_document_returns_queued(monkeypatch) -> None:
    app = _app_with_overrides()
    monkeypatch.setattr(
        f"{DOCS_MODULE}.upload_document_for_user",
        lambda db, user, storage, *, filename, content_type, data: _document(filename=filename),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("taxes.pdf", b"hello", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "queued"
    assert response.json()["filename"] == "taxes.pdf"


def test_upload_rejects_unsupported_extension() -> None:
    app = _app_with_overrides()

    client = TestClient(app)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("malware.exe", b"data", "application/octet-stream")},
    )

    assert response.status_code == 415


def test_get_missing_document_returns_404(monkeypatch) -> None:
    app = _app_with_overrides()
    monkeypatch.setattr(f"{DOCS_MODULE}.get_document_for_user", lambda *a, **k: None)

    client = TestClient(app)
    response = client.get(f"/api/v1/documents/{uuid4()}")

    assert response.status_code == 404


def test_delete_document_returns_204(monkeypatch) -> None:
    app = _app_with_overrides()
    document = _document()
    app.dependency_overrides[get_owned_document] = lambda: document
    monkeypatch.setattr(f"{DOCS_MODULE}.delete_document_for_user", lambda *a, **k: None)

    client = TestClient(app)
    response = client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 204
