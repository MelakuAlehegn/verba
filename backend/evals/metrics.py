"""Pure retrieval metrics — no I/O, so they unit-test without any API calls.

A "result" is one question's ranked list of retrieved document names against the
set of documents that actually answer it. From that we derive the usual
retrieval-quality numbers plus a diversity measure (how many distinct documents
the top-k spans), which is what MMR reranking is meant to improve.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass
class RetrievalResult:
    question: str
    expected: set[str]
    retrieved: list[str]  # document names, best-ranked first

    @property
    def hit(self) -> bool:
        """Did any expected document make the top-k?"""
        return any(name in self.expected for name in self.retrieved)

    @property
    def reciprocal_rank(self) -> float:
        """1 / rank of the first expected document (0 if none retrieved)."""
        for rank, name in enumerate(self.retrieved, start=1):
            if name in self.expected:
                return 1.0 / rank
        return 0.0

    @property
    def distinct_docs(self) -> int:
        """How many distinct documents the top-k covers (diversity)."""
        return len(set(self.retrieved))


@dataclass
class Summary:
    n: int
    hit_rate: float
    mrr: float
    mean_distinct_docs: float


def summarize(results: list[RetrievalResult]) -> Summary:
    if not results:
        return Summary(n=0, hit_rate=0.0, mrr=0.0, mean_distinct_docs=0.0)
    return Summary(
        n=len(results),
        hit_rate=mean(1.0 if result.hit else 0.0 for result in results),
        mrr=mean(result.reciprocal_rank for result in results),
        mean_distinct_docs=mean(result.distinct_docs for result in results),
    )
