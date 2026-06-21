from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services.ingestion_service import ingest_document

MODULE = "app.services.ingestion_service"


def _fake_embedder() -> SimpleNamespace:
    return SimpleNamespace(
        model="gemini-embed",
        version="v1",
        dimension=3,
        embed_documents=lambda texts: [[0.1, 0.2, 0.3] for _ in texts],
    )


def _patch_crud(monkeypatch, document) -> dict:
    calls = {"chunks": 0, "embeddings": 0}
    monkeypatch.setattr(f"{MODULE}.get_document_by_id", lambda db, did: document)
    monkeypatch.setattr(f"{MODULE}.mark_document_processing", lambda db, doc: doc)
    monkeypatch.setattr(f"{MODULE}.delete_chunks_for_document", lambda db, did: None)

    def fake_chunk(db, **kwargs):
        calls["chunks"] += 1
        return SimpleNamespace(id=uuid4())

    def fake_embedding(db, **kwargs):
        calls["embeddings"] += 1
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(f"{MODULE}.create_document_chunk", fake_chunk)
    monkeypatch.setattr(f"{MODULE}.create_chunk_embedding", fake_embedding)
    return calls


def test_ingest_success_writes_chunks_and_marks_ready(monkeypatch) -> None:
    document = SimpleNamespace(
        id=uuid4(), user_id=uuid4(), status="queued", storage_key="k", filename="note.md"
    )
    calls = _patch_crud(monkeypatch, document)
    ready = Mock()
    monkeypatch.setattr(f"{MODULE}.mark_document_ready", ready)

    storage = Mock()
    storage.get_object.return_value = b"First paragraph.\n\nSecond paragraph."
    vector_store = Mock()

    ingest_document(
        Mock(), document.id, storage=storage, embedder=_fake_embedder(), vector_store=vector_store
    )

    assert calls["chunks"] == 1  # short text → one chunk
    assert calls["embeddings"] == 1
    vector_store.ensure_collection.assert_called_once()
    vector_store.upsert.assert_called_once()
    assert len(vector_store.upsert.call_args.args[0]) == 1  # one VectorPoint
    ready.assert_called_once()
    assert ready.call_args.kwargs["chunk_count"] == 1


def test_ingest_marks_failed_on_parse_error(monkeypatch) -> None:
    document = SimpleNamespace(
        id=uuid4(), user_id=uuid4(), status="queued", storage_key="k", filename="note.md"
    )
    _patch_crud(monkeypatch, document)
    failed = Mock()
    monkeypatch.setattr(f"{MODULE}.mark_document_failed", failed)

    def boom(data, *, filename):
        raise ValueError("bad bytes")

    monkeypatch.setattr(f"{MODULE}.extract_text", boom)

    storage = Mock()
    storage.get_object.return_value = b"whatever"

    ingest_document(
        Mock(), document.id, storage=storage, embedder=_fake_embedder(), vector_store=Mock()
    )

    failed.assert_called_once()
    assert failed.call_args.kwargs["error_code"] == "ingestion_error"


def test_ingest_skips_when_already_ready(monkeypatch) -> None:
    document = SimpleNamespace(id=uuid4(), status="ready")
    monkeypatch.setattr(f"{MODULE}.get_document_by_id", lambda db, did: document)
    processing = Mock()
    monkeypatch.setattr(f"{MODULE}.mark_document_processing", processing)

    ingest_document(
        Mock(), document.id, storage=Mock(), embedder=_fake_embedder(), vector_store=Mock()
    )

    processing.assert_not_called()
