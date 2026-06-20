"""Turn text into vectors for similarity search.

The `Embedder` protocol is the swappable seam — a Gemini implementation now,
but OpenAI / a local model / a test fake all satisfy the same contract. The
worker and retrieval code depend on the protocol, never on Gemini directly.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Protocol

from google import genai
from google.genai import types

from app.core.config import Settings, get_settings


class Embedder(Protocol):
    model: str
    version: str
    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


def l2_normalize(vector: list[float]) -> list[float]:
    # Gemini doesn't auto-normalize when output_dimensionality < 3072, and
    # cosine similarity assumes unit vectors — so we normalize ourselves.
    norm = math.sqrt(sum(component * component for component in vector))
    if norm == 0.0:
        return vector
    return [component / norm for component in vector]


class GeminiEmbedder:
    """Embeds via Google's Gemini API.

    Documents and queries use different task types (RETRIEVAL_DOCUMENT vs
    RETRIEVAL_QUERY) — Gemini tunes the embedding for each role, which lifts
    retrieval quality over using one type for both.
    """

    def __init__(self, settings: Settings) -> None:
        self.model = settings.embedding_model
        self.version = settings.embedding_version
        self.dimension = settings.embedding_dimension
        self._client = genai.Client(api_key=settings.google_api_key)

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        response = self._client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self.dimension,
            ),
        )
        return [l2_normalize(list(embedding.values)) for embedding in response.embeddings]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return GeminiEmbedder(get_settings())
