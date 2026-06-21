"""LLM text generation, streamed token-by-token.

`LLMProvider` is the swappable seam — Gemini now, Groq/others later — mirroring
the `Embedder` pattern. Generation streams so the API can relay tokens over SSE
as they arrive rather than waiting for the whole answer.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Protocol

from google import genai

from app.core.config import Settings, get_settings


class LLMProvider(Protocol):
    model: str

    def stream(self, prompt: str) -> Iterator[str]: ...


class GeminiLLM:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.generation_model
        self._client = genai.Client(api_key=settings.google_api_key)

    def stream(self, prompt: str) -> Iterator[str]:
        responses = self._client.models.generate_content_stream(
            model=self.model,
            contents=prompt,
        )
        for chunk in responses:
            # Some streamed chunks carry no text (e.g. metadata-only) — skip them.
            if chunk.text:
                yield chunk.text


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    return GeminiLLM(get_settings())
