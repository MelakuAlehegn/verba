from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services.rag.vector_store import (
    QdrantVectorStore,
    VectorMatch,
    VectorPoint,
)


class FakeVectorStore:
    """In-memory stand-in for tests of higher layers (worker, retrieval)."""

    def __init__(self) -> None:
        self.points: list[VectorPoint] = []

    def health_check(self) -> None:
        pass

    def ensure_collection(self) -> None:
        pass

    def upsert(self, points) -> None:
        self.points.extend(points)

    def search(self, vector, *, user_id, document_ids=None, limit=8, with_vectors=False):
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b, strict=False))

        candidates = [p for p in self.points if p.user_id == user_id]
        if document_ids is not None:
            doc_set = set(document_ids)
            candidates = [p for p in candidates if p.document_id in doc_set]
        ranked = sorted(candidates, key=lambda p: dot(vector, p.vector), reverse=True)
        return [
            VectorMatch(
                chunk_id=p.chunk_id,
                score=dot(vector, p.vector),
                vector=list(p.vector) if with_vectors else None,
            )
            for p in ranked[:limit]
        ]

    def get_vectors(self, chunk_ids):
        wanted = set(chunk_ids)
        return {p.chunk_id: list(p.vector) for p in self.points if p.chunk_id in wanted}

    def delete_document(self, document_id) -> None:
        self.points = [p for p in self.points if p.document_id != document_id]


def _point(user_id, vector) -> VectorPoint:
    return VectorPoint(chunk_id=uuid4(), document_id=uuid4(), user_id=user_id, vector=vector)


def test_fake_store_filters_by_tenant() -> None:
    store = FakeVectorStore()
    alice, bob = uuid4(), uuid4()
    store.upsert([_point(alice, [1.0, 0.0]), _point(bob, [1.0, 0.0])])

    matches = store.search([1.0, 0.0], user_id=alice)

    assert len(matches) == 1  # Bob's identical vector is invisible to Alice


def test_fake_store_ranks_by_similarity() -> None:
    store = FakeVectorStore()
    user = uuid4()
    near = _point(user, [1.0, 0.0])
    far = _point(user, [0.0, 1.0])
    store.upsert([far, near])

    matches = store.search([1.0, 0.0], user_id=user, limit=2)

    assert matches[0].chunk_id == near.chunk_id  # aligned vector ranks first


def _qdrant_store_with_mock() -> tuple[QdrantVectorStore, Mock]:
    store = QdrantVectorStore.__new__(QdrantVectorStore)  # bypass real client init
    client = Mock()
    store._client = client
    store._collection = "document_chunks"
    store._dimension = 768
    return store, client


def test_ensure_collection_creates_when_missing() -> None:
    store, client = _qdrant_store_with_mock()
    client.collection_exists.return_value = False

    store.ensure_collection()

    client.create_collection.assert_called_once()
    assert client.create_payload_index.call_count == 2  # user_id + document_id


def test_ensure_collection_skips_when_present() -> None:
    store, client = _qdrant_store_with_mock()
    client.collection_exists.return_value = True

    store.ensure_collection()

    client.create_collection.assert_not_called()


def test_search_filters_by_user_and_parses_matches() -> None:
    store, client = _qdrant_store_with_mock()
    chunk_id = uuid4()
    client.query_points.return_value = SimpleNamespace(
        points=[SimpleNamespace(payload={"chunk_id": str(chunk_id)}, score=0.9)]
    )
    user_id = uuid4()

    matches = store.search([0.1, 0.2], user_id=user_id, limit=5)

    assert matches == [VectorMatch(chunk_id=chunk_id, score=0.9)]
    assert matches[0].vector is None  # not requested → not carried
    assert client.query_points.call_args.kwargs["with_vectors"] is False
    query_filter = client.query_points.call_args.kwargs["query_filter"]
    assert any(condition.key == "user_id" for condition in query_filter.must)


def test_search_carries_vectors_when_requested() -> None:
    store, client = _qdrant_store_with_mock()
    chunk_id = uuid4()
    client.query_points.return_value = SimpleNamespace(
        points=[
            SimpleNamespace(payload={"chunk_id": str(chunk_id)}, score=0.9, vector=[0.1, 0.2])
        ]
    )

    matches = store.search([0.1, 0.2], user_id=uuid4(), limit=5, with_vectors=True)

    assert matches[0].vector == [0.1, 0.2]
    assert client.query_points.call_args.kwargs["with_vectors"] is True
