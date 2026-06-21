from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services.rag.retrieval import retrieve_context
from app.services.rag.vector_store import VectorMatch

MODULE = "app.services.rag.retrieval"


def _embedder() -> SimpleNamespace:
    return SimpleNamespace(embed_query=lambda text: [0.1, 0.2, 0.3])


def _row(chunk_id, content) -> SimpleNamespace:
    return SimpleNamespace(
        id=chunk_id, document_id=uuid4(), content=content, chunk_metadata={"page": 1}
    )


def test_retrieve_preserves_qdrant_ranking(monkeypatch) -> None:
    user_id = uuid4()
    high, low = uuid4(), uuid4()
    vector_store = Mock()
    vector_store.search.return_value = [
        VectorMatch(chunk_id=high, score=0.9),
        VectorMatch(chunk_id=low, score=0.4),
    ]
    # DB returns rows in the *opposite* order to prove we re-sort by score.
    monkeypatch.setattr(
        f"{MODULE}.get_chunks_by_ids",
        lambda db, ids, uid: [_row(low, "less relevant"), _row(high, "most relevant")],
    )

    results = retrieve_context(
        Mock(), user_id=user_id, query="q", embedder=_embedder(), vector_store=vector_store
    )

    assert [r.chunk_id for r in results] == [high, low]
    assert results[0].content == "most relevant"


def test_retrieve_skips_chunks_missing_from_postgres(monkeypatch) -> None:
    present, drifted = uuid4(), uuid4()
    vector_store = Mock()
    vector_store.search.return_value = [
        VectorMatch(chunk_id=present, score=0.8),
        VectorMatch(chunk_id=drifted, score=0.7),
    ]
    monkeypatch.setattr(f"{MODULE}.get_chunks_by_ids", lambda db, ids, uid: [_row(present, "here")])

    results = retrieve_context(
        Mock(), user_id=uuid4(), query="q", embedder=_embedder(), vector_store=vector_store
    )

    assert [r.chunk_id for r in results] == [present]  # drifted vector skipped


def test_retrieve_returns_empty_when_no_matches() -> None:
    vector_store = Mock()
    vector_store.search.return_value = []

    results = retrieve_context(
        Mock(), user_id=uuid4(), query="q", embedder=_embedder(), vector_store=vector_store
    )

    assert results == []


def test_retrieve_filters_by_tenant(monkeypatch) -> None:
    user_id = uuid4()
    chunk_id = uuid4()
    vector_store = Mock()
    vector_store.search.return_value = [VectorMatch(chunk_id=chunk_id, score=0.9)]
    captured = {}

    def fake_get(db, ids, uid):
        captured["user_id"] = uid
        return [_row(chunk_id, "text")]

    monkeypatch.setattr(f"{MODULE}.get_chunks_by_ids", fake_get)

    retrieve_context(
        Mock(), user_id=user_id, query="q", embedder=_embedder(), vector_store=vector_store
    )

    # Both Qdrant and the Postgres fetch are scoped to the user.
    assert captured["user_id"] == user_id
    assert vector_store.search.call_args.kwargs["user_id"] == user_id
