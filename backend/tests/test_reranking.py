from uuid import uuid4

from app.services.rag.reranking import mmr_rerank
from app.services.rag.vector_store import VectorMatch


def _match(score, vector) -> VectorMatch:
    return VectorMatch(chunk_id=uuid4(), score=score, vector=vector)


def test_mmr_pure_relevance_orders_by_score() -> None:
    # λ = 1.0 → the diversity term vanishes, so MMR is just relevance ranking.
    a = _match(0.90, [1.0, 0.0])
    b = _match(0.85, [1.0, 0.0])
    c = _match(0.80, [0.0, 1.0])

    ranked = mmr_rerank([c, a, b], limit=3, lambda_mult=1.0)

    assert ranked == [a, b, c]


def test_mmr_promotes_a_diverse_chunk_over_a_near_duplicate() -> None:
    a = _match(0.90, [1.0, 0.0])  # most relevant
    b = _match(0.85, [1.0, 0.0])  # near-duplicate of a → redundant
    c = _match(0.80, [0.0, 1.0])  # lower score but orthogonal → diverse

    ranked = mmr_rerank([a, b, c], limit=3, lambda_mult=0.7)

    # a picked first (top relevance), then c beats b despite b's higher score
    # because b just repeats a.
    assert ranked == [a, c, b]


def test_mmr_truncates_to_limit() -> None:
    a = _match(0.90, [1.0, 0.0])
    b = _match(0.85, [1.0, 0.0])
    c = _match(0.80, [0.0, 1.0])

    ranked = mmr_rerank([a, b, c], limit=2, lambda_mult=0.7)

    assert ranked == [a, c]


def test_mmr_handles_empty_input() -> None:
    assert mmr_rerank([], limit=5, lambda_mult=0.7) == []
