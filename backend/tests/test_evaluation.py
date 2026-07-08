from evals.metrics import RetrievalResult, summarize


def test_hit_reciprocal_rank_and_distinct() -> None:
    result = RetrievalResult("q", {"a.md"}, ["b.md", "a.md", "c.md"])
    assert result.hit is True
    assert result.reciprocal_rank == 0.5  # expected doc is 2nd
    assert result.distinct_docs == 3


def test_miss_scores_zero() -> None:
    result = RetrievalResult("q", {"a.md"}, ["b.md", "c.md"])
    assert result.hit is False
    assert result.reciprocal_rank == 0.0


def test_distinct_counts_unique_docs() -> None:
    # A top-k stacked with one document (what MMR fights) scores low diversity.
    result = RetrievalResult("q", {"a.md"}, ["a.md", "a.md", "a.md"])
    assert result.distinct_docs == 1


def test_summarize_aggregates() -> None:
    results = [
        RetrievalResult("q1", {"a"}, ["a"]),  # hit, rr 1.0, distinct 1
        RetrievalResult("q2", {"b"}, ["a", "b"]),  # hit, rr 0.5, distinct 2
        RetrievalResult("q3", {"c"}, ["a", "b"]),  # miss, rr 0.0, distinct 2
    ]
    summary = summarize(results)
    assert summary.n == 3
    assert abs(summary.hit_rate - 2 / 3) < 1e-9
    assert abs(summary.mrr - (1.0 + 0.5 + 0.0) / 3) < 1e-9
    assert abs(summary.mean_distinct_docs - (1 + 2 + 2) / 3) < 1e-9


def test_summarize_empty() -> None:
    summary = summarize([])
    assert summary.n == 0
    assert summary.hit_rate == 0.0
    assert summary.mrr == 0.0
