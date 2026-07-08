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

from app.crud.document_chunk import get_chunks_by_ids, search_chunks_by_keyword
from app.services.rag.embedding import Embedder
from app.services.rag.fusion import reciprocal_rank_fusion
from app.services.rag.reranking import mmr_rerank
from app.services.rag.vector_store import VectorMatch, VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: dict[str, object]


def _hybrid_candidates(
    db: Session,
    *,
    query: str,
    vector_relevant: list[VectorMatch],
    user_id: UUID,
    document_ids: Iterable[UUID] | None,
    limit: int,
    vector_store: VectorStore,
    need_vectors: bool,
) -> list[VectorMatch]:
    """Fuse the vector ranking with a keyword (full-text) ranking via RRF.

    Returns candidates scored by their fused rank. When MMR will run
    (`need_vectors`), keyword-only hits lack an embedding, so we fetch those from
    the vector store to keep reranking uniform.
    """
    vector_ids = [match.chunk_id for match in vector_relevant]
    vector_by_id = {match.chunk_id: match for match in vector_relevant}
    keyword_ids = search_chunks_by_keyword(
        db, user_id=user_id, query=query, document_ids=document_ids, limit=limit
    )
    fused = reciprocal_rank_fusion([vector_ids, keyword_ids])[:limit]
    logger.info(
        "hybrid: %d vector + %d keyword → %d fused",
        len(vector_ids),
        len(keyword_ids),
        len(fused),
    )
    if not fused:
        return []

    extra_vectors: dict[UUID, list[float]] = {}
    if need_vectors:
        missing = [
            chunk_id
            for chunk_id, _ in fused
            if vector_by_id.get(chunk_id) is None or vector_by_id[chunk_id].vector is None
        ]
        extra_vectors = vector_store.get_vectors(missing) if missing else {}

    candidates: list[VectorMatch] = []
    for chunk_id, rrf_score in fused:
        existing = vector_by_id.get(chunk_id)
        vector = existing.vector if existing and existing.vector is not None else None
        if vector is None:
            vector = extra_vectors.get(chunk_id)
        candidates.append(VectorMatch(chunk_id=chunk_id, score=rrf_score, vector=vector))
    return candidates


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
    candidate_pool: int = 0,
    mmr_lambda: float = 0.7,
    hybrid: bool = False,
) -> list[RetrievedChunk]:
    # Reranking over-fetches a wider candidate pool, then MMR picks `limit` of
    # them by relevance + diversity. Disabled (pool <= limit) → fetch exactly
    # `limit` and skip the extra vector payload.
    reranking = candidate_pool > limit
    fetch_limit = candidate_pool if reranking else limit

    query_vector = embedder.embed_query(query)
    matches = vector_store.search(
        query_vector,
        user_id=user_id,
        document_ids=document_ids,
        limit=fetch_limit,
        with_vectors=reranking,
    )

    # Drop weak matches: an off-topic question still returns the nearest vectors,
    # but at low similarity — feeding them as "context" invites the model to
    # answer from general knowledge. Below the threshold, drop them so an
    # off-topic question yields empty context and a grounded "I don't know".
    top_score = matches[0].score if matches else 0.0
    relevant = [match for match in matches if match.score >= min_score]
    logger.info(
        "retrieval: %d matches, top score %.3f, %d kept (threshold %.2f)",
        len(matches),
        top_score,
        len(relevant),
        min_score,
    )

    # Hybrid: add a keyword arm and fuse. Keyword hits stand on their own (a real
    # lexical match), so they can rescue an exact term the vector arm ranked low.
    if hybrid:
        relevant = _hybrid_candidates(
            db,
            query=query,
            vector_relevant=relevant,
            user_id=user_id,
            document_ids=document_ids,
            limit=fetch_limit,
            vector_store=vector_store,
            need_vectors=reranking,
        )

    if not relevant:
        return []

    # Rerank when we actually fetched candidate vectors; otherwise keep Qdrant's
    # relevance order and just cap at `limit`.
    if reranking and all(match.vector is not None for match in relevant):
        pool = relevant
        relevant = mmr_rerank(pool, limit=limit, lambda_mult=mmr_lambda)
        # Show the reorder: each kept chunk as (its pure-relevance rank, score).
        # Non-sequential ranks mean MMR pulled in a lower-ranked but more diverse
        # chunk over a higher-scored near-duplicate.
        rank_by_id = {match.chunk_id: i for i, match in enumerate(pool, start=1)}
        logger.info(
            "MMR rerank (λ=%.2f): %d candidates → kept %d; order [rank:score] = %s",
            mmr_lambda,
            len(pool),
            len(relevant),
            [f"{rank_by_id[m.chunk_id]}:{m.score:.3f}" for m in relevant],
        )
    else:
        relevant = relevant[:limit]

    rows = get_chunks_by_ids(db, [match.chunk_id for match in relevant], user_id)
    by_id = {row.id: row for row in rows}

    # Preserve the ranking we settled on above (MMR, or Qdrant similarity when
    # reranking is off) — the IN-query order isn't sorted — and drop any vector
    # whose Postgres row is gone (store drift).
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
