"""Reciprocal Rank Fusion (RRF) — merge several ranked lists into one.

Hybrid retrieval produces two rankings of the same chunks (vector similarity and
keyword relevance) whose raw scores aren't comparable — a 0.82 cosine means
nothing next to a ts_rank of 0.06. RRF sidesteps that by scoring on *rank*
alone: a chunk's fused score is the sum over each list of 1/(k + rank), so
appearing near the top of either list lifts it, and appearing in both lifts it
more. `k` (conventionally 60) damps the influence of the very top ranks so a
single list can't dominate.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

RRF_K = 60


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[UUID]],
    *,
    k: int = RRF_K,
) -> list[tuple[UUID, float]]:
    """Fuse ranked id lists into one list of (id, score), best-first.

    Each input list is assumed already ordered best-to-worst. Ids may appear in
    any subset of the lists; the result is de-duplicated.
    """
    scores: dict[UUID, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
