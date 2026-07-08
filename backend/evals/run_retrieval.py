"""Retrieval eval — grade ranking quality, baseline (cosine) vs MMR.

Makes real Gemini *embedding* calls only (no generation), on the small in-repo
corpus, so it's cheap to run manually:

    python -m evals.run_retrieval

We use a deliberately small top-k (EVAL_TOP_K) so the corpus size doesn't make
every question trivially "hit" — ranking has to actually choose. MMR should
match or beat baseline on hit@k/MRR while covering more distinct documents.
"""

from __future__ import annotations

from uuid import uuid4

from app.core.config import get_settings
from app.services.rag.chunking import chunk_text
from app.services.rag.embedding import get_embedder
from app.services.rag.reranking import mmr_rerank
from app.services.rag.vector_store import VectorMatch
from evals.dataset import CASES, CORPUS
from evals.metrics import RetrievalResult, summarize

EVAL_TOP_K = 3
EVAL_POOL = 12  # candidates fetched before MMR trims to EVAL_TOP_K
# Fine-grained chunking so short fixture docs yield several chunks to rank.
CHUNK_TOKENS = 48
CHUNK_OVERLAP = 8


def _cosine(a: list[float], b: list[float]) -> float:
    # Embeddings are L2-normalized upstream, so dot product == cosine similarity.
    return sum(x * y for x, y in zip(a, b, strict=False))


def build_index(embedder) -> tuple[list[VectorMatch], dict]:
    """Embed every corpus chunk. Returns candidate matches (score filled per
    query later) and a chunk_id → document-name map."""
    chunks: list[tuple] = []  # (chunk_id, doc_name, vector)
    for doc in CORPUS:
        pieces = chunk_text(doc.text, max_tokens=CHUNK_TOKENS, overlap_tokens=CHUNK_OVERLAP)
        vectors = embedder.embed_documents([piece.content for piece in pieces])
        for vector in vectors:
            chunks.append((uuid4(), doc.name, vector))
    name_by_id = {chunk_id: name for chunk_id, name, _ in chunks}
    return chunks, name_by_id


def rank(
    query: str, chunks: list[tuple], name_by_id: dict, embedder, *, use_mmr: bool
) -> list[str]:
    query_vector = embedder.embed_query(query)
    matches = [
        VectorMatch(chunk_id=chunk_id, score=_cosine(query_vector, vector), vector=vector)
        for chunk_id, _, vector in chunks
    ]
    matches.sort(key=lambda match: match.score, reverse=True)
    if use_mmr:
        settings = get_settings()
        selected = mmr_rerank(
            matches[:EVAL_POOL], limit=EVAL_TOP_K, lambda_mult=settings.mmr_lambda
        )
    else:
        selected = matches[:EVAL_TOP_K]
    return [name_by_id[match.chunk_id] for match in selected]


def evaluate(chunks, name_by_id, embedder, *, use_mmr: bool) -> list[RetrievalResult]:
    results = []
    for case in CASES:
        retrieved = rank(case.question, chunks, name_by_id, embedder, use_mmr=use_mmr)
        results.append(
            RetrievalResult(
                question=case.question,
                expected=set(case.expected_docs),
                retrieved=retrieved,
            )
        )
    return results


def main() -> None:
    settings = get_settings()
    embedder = get_embedder()
    print(
        f"corpus: {len(CORPUS)} docs, {len(CASES)} questions | "
        f"top_k={EVAL_TOP_K}, pool={EVAL_POOL}, mmr_lambda={settings.mmr_lambda}\n"
    )
    chunks, name_by_id = build_index(embedder)
    print(f"indexed {len(chunks)} chunks\n")

    for label, use_mmr in (("baseline (cosine)", False), ("MMR rerank", True)):
        summary = summarize(evaluate(chunks, name_by_id, embedder, use_mmr=use_mmr))
        print(
            f"{label:20s}  hit@{EVAL_TOP_K}={summary.hit_rate:.2f}  "
            f"MRR={summary.mrr:.3f}  mean_distinct_docs={summary.mean_distinct_docs:.2f}"
        )

    print("\nper-question (MMR):")
    for result in evaluate(chunks, name_by_id, embedder, use_mmr=True):
        mark = "✓" if result.hit else "✗"
        print(f"  {mark} rr={result.reciprocal_rank:.2f}  {result.question}")


if __name__ == "__main__":
    main()
