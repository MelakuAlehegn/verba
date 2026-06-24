"""Retrieve the chunks most relevant to a query.

The read half of RAG: embed the question, find nearest vectors in Qdrant
(filtered to the user and, optionally, a set of documents), then load the
matching chunk *text* from Postgres. Qdrant ranks; Postgres supplies content.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.document_chunk import get_chunks_by_ids
from app.services.rag.embedding import Embedder
from app.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: dict[str, object]


def retrieve_context(
    db: Session,
    *,
    user_id: UUID,
    query: str,
    embedder: Embedder,
    vector_store: VectorStore,
    document_ids: Iterable[UUID] | None = None,
    limit: int = 8,
    min_score: float = 0.0,
) -> list[RetrievedChunk]:
    query_vector = embedder.embed_query(query)
    matches = vector_store.search(
        query_vector, user_id=user_id, document_ids=document_ids, limit=limit
    )
    if not matches:
        return []

    # Drop weak matches: an off-topic question still returns the nearest vectors,
    # but at low similarity — feeding them as "context" invites the model to
    # answer from general knowledge. Below the threshold, return nothing so the
    # answer is a grounded "I don't know".
    top_score = matches[0].score
    relevant = [match for match in matches if match.score >= min_score]
    logger.info(
        "retrieval: %d matches, top score %.3f, %d kept (threshold %.2f)",
        len(matches),
        top_score,
        len(relevant),
        min_score,
    )
    if not relevant:
        return []

    rows = get_chunks_by_ids(db, [match.chunk_id for match in relevant], user_id)
    by_id = {row.id: row for row in rows}

    # Preserve Qdrant's similarity ranking (the IN-query order isn't sorted),
    # and drop any vector whose Postgres row is gone (store drift).
    results: list[RetrievedChunk] = []
    for match in relevant:
        row = by_id.get(match.chunk_id)
        if row is None:
            continue
        results.append(
            RetrievedChunk(
                chunk_id=row.id,
                document_id=row.document_id,
                content=row.content,
                score=match.score,
                metadata=row.chunk_metadata,
            )
        )
    return results
