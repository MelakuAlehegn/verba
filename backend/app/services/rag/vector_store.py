"""Vector storage + similarity search over Qdrant.

Qdrant is a *derived index*: the point id equals the Postgres `chunk_id`, and
the payload carries `user_id`/`document_id` so every search can be tenant- and
scope-filtered before ranking. The `VectorStore` protocol keeps it swappable
(and lets tests use an in-memory fake).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import Settings, get_settings


@dataclass
class VectorPoint:
    chunk_id: UUID
    document_id: UUID
    user_id: UUID
    vector: list[float]


@dataclass
class VectorMatch:
    chunk_id: UUID
    score: float
    # Populated only when search(..., with_vectors=True). MMR reranking needs the
    # candidate vectors to measure redundancy between chunks; ordinary retrieval
    # leaves it None to avoid shipping vectors over the wire.
    vector: list[float] | None = None


class VectorStore(Protocol):
    def ensure_collection(self) -> None: ...

    def upsert(self, points: Sequence[VectorPoint]) -> None: ...

    def search(
        self,
        vector: list[float],
        *,
        user_id: UUID,
        document_ids: Iterable[UUID] | None = None,
        limit: int = 8,
        with_vectors: bool = False,
    ) -> list[VectorMatch]: ...

    def delete_document(self, document_id: UUID) -> None: ...


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        self._client = QdrantClient(url=settings.qdrant_url)
        self._collection = settings.qdrant_collection
        self._dimension = settings.embedding_dimension

    def ensure_collection(self) -> None:
        if self._client.collection_exists(self._collection):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=VectorParams(size=self._dimension, distance=Distance.COSINE),
        )
        # Indexed payload fields → fast filtering before similarity ranking.
        for field in ("user_id", "document_id"):
            self._client.create_payload_index(
                collection_name=self._collection,
                field_name=field,
                field_schema="keyword",
            )

    def upsert(self, points: Sequence[VectorPoint]) -> None:
        if not points:
            return
        self._client.upsert(
            collection_name=self._collection,
            points=[
                PointStruct(
                    id=str(point.chunk_id),
                    vector=point.vector,
                    payload={
                        "user_id": str(point.user_id),
                        "document_id": str(point.document_id),
                        "chunk_id": str(point.chunk_id),
                    },
                )
                for point in points
            ],
        )

    def search(
        self,
        vector: list[float],
        *,
        user_id: UUID,
        document_ids: Iterable[UUID] | None = None,
        limit: int = 8,
        with_vectors: bool = False,
    ) -> list[VectorMatch]:
        # Tenant filter is mandatory; document scope is optional (chat scoping).
        conditions = [FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
        if document_ids is not None:
            ids = [str(document_id) for document_id in document_ids]
            conditions.append(FieldCondition(key="document_id", match=MatchAny(any=ids)))

        response = self._client.query_points(
            collection_name=self._collection,
            query=vector,
            query_filter=Filter(must=conditions),
            limit=limit,
            with_vectors=with_vectors,
        )
        return [
            VectorMatch(
                chunk_id=UUID(point.payload["chunk_id"]),
                score=point.score,
                vector=list(point.vector) if with_vectors else None,
            )
            for point in response.points
        ]

    def delete_document(self, document_id: UUID) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=str(document_id))
                    )
                ]
            ),
        )


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    return QdrantVectorStore(get_settings())
