import math

from app.services.rag.embedding import Embedder, l2_normalize


def test_l2_normalize_returns_unit_vector() -> None:
    normalized = l2_normalize([3.0, 4.0])
    assert math.isclose(math.sqrt(sum(c * c for c in normalized)), 1.0)
    assert math.isclose(normalized[0], 0.6)
    assert math.isclose(normalized[1], 0.8)


def test_l2_normalize_handles_zero_vector() -> None:
    assert l2_normalize([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


class FakeEmbedder:
    """Deterministic stand-in so tests never touch the real Gemini API."""

    model = "fake"
    version = "v0"
    dimension = 3

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(t)), 0.0, 0.0] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text)), 0.0, 0.0]


def test_fake_embedder_satisfies_protocol() -> None:
    # A structural check: anything with the right shape is an Embedder.
    embedder: Embedder = FakeEmbedder()
    docs = embedder.embed_documents(["ab", "abcd"])
    assert len(docs) == 2
    assert all(len(v) == embedder.dimension for v in docs)
    assert len(embedder.embed_query("xyz")) == embedder.dimension
