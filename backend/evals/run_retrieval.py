"""Retrieval eval — grade ranking quality across baseline / MMR / hybrid.

Makes real Gemini *embedding* calls only (no generation), on the small in-repo
corpus, so it's cheap to run manually:

    python -m evals.run_retrieval

Modes:
- baseline : pure cosine top-k
- MMR      : cosine candidates reranked for diversity
- hybrid   : cosine fused (RRF) with a keyword arm, then top-k

The keyword arm here is a simple in-memory token-overlap scorer standing in for
the production Postgres full-text search — enough to show the fusion effect and
where exact-term queries (AES-256, TLS 1.3) benefit. We use a deliberately small
top-k so ranking actually has to choose.
"""

from __future__ import annotations

import re
from uuid import uuid4

from app.core.config import get_settings
from app.services.rag.chunking import chunk_text
from app.services.rag.embedding import get_embedder
from app.services.rag.fusion import reciprocal_rank_fusion
from app.services.rag.reranking import mmr_rerank
from app.services.rag.vector_store import VectorMatch
from evals.dataset import CASES, CORPUS
from evals.metrics import RetrievalResult, summarize

EVAL_TOP_K = 3
EVAL_POOL = 12  # candidates fetched before MMR/fusion trims to EVAL_TOP_K
CHUNK_TOKENS = 48
CHUNK_OVERLAP = 8


def _cosine(a: list[float], b: list[float]) -> float:
    # Embeddings are L2-normalized upstream, so dot product == cosine similarity.
    return sum(x * y for x, y in zip(a, b, strict=False))


def _tokens(text: str) -> list[str]:
    return [token for token in re.split(r"\W+", text.lower()) if token]


def build_index(embedder) -> tuple[list[tuple], dict]:
    """Embed every corpus chunk. Returns (chunk_id, doc_name, text, vector) rows
    and a chunk_id → document-name map."""
    chunks: list[tuple] = []
    for doc in CORPUS:
        pieces = chunk_text(doc.text, max_tokens=CHUNK_TOKENS, overlap_tokens=CHUNK_OVERLAP)
        vectors = embedder.embed_documents([piece.content for piece in pieces])
        for piece, vector in zip(pieces, vectors, strict=True):
            chunks.append((uuid4(), doc.name, piece.content, vector))
    name_by_id = {chunk_id: name for chunk_id, name, _, _ in chunks}
    return chunks, name_by_id


def _vector_ranked(query_vector, chunks) -> list[VectorMatch]:
    matches = [
        VectorMatch(chunk_id=chunk_id, score=_cosine(query_vector, vector), vector=vector)
        for chunk_id, _, _, vector in chunks
    ]
    matches.sort(key=lambda match: match.score, reverse=True)
    return matches


def _keyword_ranked(query: str, chunks) -> list:
    query_terms = set(_tokens(query))
    scored = []
    for chunk_id, _, text, _ in chunks:
        overlap = sum(1 for token in _tokens(text) if token in query_terms)
        if overlap:
            scored.append((overlap, chunk_id))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk_id for _, chunk_id in scored]


def retrieve(mode: str, query: str, chunks, name_by_id, embedder) -> list[str]:
    settings = get_settings()
    vector_matches = _vector_ranked(embedder.embed_query(query), chunks)

    if mode == "baseline":
        selected = [m.chunk_id for m in vector_matches[:EVAL_TOP_K]]
    elif mode == "mmr":
        reranked = mmr_rerank(
            vector_matches[:EVAL_POOL], limit=EVAL_TOP_K, lambda_mult=settings.mmr_lambda
        )
        selected = [m.chunk_id for m in reranked]
    elif mode == "hybrid":
        vector_ids = [m.chunk_id for m in vector_matches[:EVAL_POOL]]
        keyword_ids = _keyword_ranked(query, chunks)[:EVAL_POOL]
        fused = reciprocal_rank_fusion([vector_ids, keyword_ids])[:EVAL_TOP_K]
        selected = [chunk_id for chunk_id, _ in fused]
    else:
        raise ValueError(mode)

    return [name_by_id[chunk_id] for chunk_id in selected]


def evaluate(mode: str, chunks, name_by_id, embedder) -> list[RetrievalResult]:
    return [
        RetrievalResult(
            question=case.question,
            expected=set(case.expected_docs),
            retrieved=retrieve(mode, case.question, chunks, name_by_id, embedder),
        )
        for case in CASES
    ]


def main() -> None:
    settings = get_settings()
    embedder = get_embedder()
    print(
        f"corpus: {len(CORPUS)} docs, {len(CASES)} questions | "
        f"top_k={EVAL_TOP_K}, pool={EVAL_POOL}, mmr_lambda={settings.mmr_lambda}\n"
    )
    chunks, name_by_id = build_index(embedder)
    print(f"indexed {len(chunks)} chunks\n")

    for label, mode in (("baseline (cosine)", "baseline"), ("MMR", "mmr"), ("hybrid", "hybrid")):
        summary = summarize(evaluate(mode, chunks, name_by_id, embedder))
        print(
            f"{label:20s}  hit@{EVAL_TOP_K}={summary.hit_rate:.2f}  "
            f"MRR={summary.mrr:.3f}  mean_distinct_docs={summary.mean_distinct_docs:.2f}"
        )

    print("\nper-question (hybrid):")
    for result in evaluate("hybrid", chunks, name_by_id, embedder):
        mark = "✓" if result.hit else "✗"
        print(f"  {mark} rr={result.reciprocal_rank:.2f}  {result.question}")


if __name__ == "__main__":
    main()
