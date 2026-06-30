"""Rerank retrieved candidates with Maximal Marginal Relevance (MMR).

Pure vector similarity returns the chunks *closest to the query*, which are
often near-duplicates of each other — three slices of the same paragraph crowd
out a second relevant passage elsewhere. MMR fixes this by picking chunks
greedily, each time maximising

    score = λ · relevance(chunk, query) − (1 − λ) · max redundancy(chunk, picked)

so every pick is both relevant *and* different from what's already chosen.
λ = 1 collapses to plain relevance ranking; λ = 0 maximises diversity. We reuse
the cosine score Qdrant already computed for the relevance term, and dot products
between candidate vectors for redundancy (embeddings are L2-normalised, so a dot
product *is* cosine similarity). No model, no API call — just arithmetic.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.services.rag.vector_store import VectorMatch


def _cosine(a: list[float], b: list[float]) -> float:
    # Vectors are L2-normalised upstream, so the dot product is cosine similarity.
    return sum(x * y for x, y in zip(a, b, strict=False))


def mmr_rerank(
    candidates: Sequence[VectorMatch],
    *,
    limit: int,
    lambda_mult: float,
) -> list[VectorMatch]:
    """Reorder `candidates` by MMR and return at most `limit` of them.

    Every candidate must carry a `vector` (search with `with_vectors=True`).
    `candidates` are assumed already filtered/sorted by relevance, but order is
    not relied upon — relevance comes from each match's cosine `score`.
    """
    selected: list[VectorMatch] = []
    remaining = list(candidates)

    while remaining and len(selected) < limit:
        best: VectorMatch | None = None
        best_mmr = float("-inf")
        for candidate in remaining:
            redundancy = max(
                (_cosine(candidate.vector, chosen.vector) for chosen in selected),
                default=0.0,
            )
            mmr = lambda_mult * candidate.score - (1.0 - lambda_mult) * redundancy
            if mmr > best_mmr:
                best_mmr = mmr
                best = candidate
        assert best is not None  # remaining is non-empty, so a best always exists
        selected.append(best)
        remaining.remove(best)

    return selected
