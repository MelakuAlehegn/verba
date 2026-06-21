"""Structure-aware text chunking for retrieval.

Splits a document into overlapping passages sized for embedding + retrieval.
We respect paragraph boundaries (split on blank lines) instead of cutting at
arbitrary character offsets, so each chunk stays semantically coherent. Chunks
overlap by a configurable budget so a fact spanning a boundary isn't lost.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Stamp on every chunk; bump when the chunking algorithm changes so stale
# chunks can be detected and re-indexed. It tracks the code, not config.
CHUNKING_VERSION = "v1"

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


@dataclass
class TextChunk:
    index: int
    content: str
    token_count: int
    metadata: dict[str, object] = field(default_factory=dict)


def count_tokens(text: str) -> int:
    """Approximate token count by whitespace words.

    A real tokenizer (e.g. tiktoken matched to the embedding model) swaps in
    here later without changing the chunking logic.
    """
    return len(text.split())


def _split_paragraphs(text: str) -> list[str]:
    return [block.strip() for block in _PARAGRAPH_BREAK.split(text.strip()) if block.strip()]


def _split_long_paragraph(paragraph: str, max_tokens: int) -> list[str]:
    # A single paragraph larger than the budget is hard-split on word windows.
    words = paragraph.split()
    return [" ".join(words[i : i + max_tokens]) for i in range(0, len(words), max_tokens)]


def _carry_overlap(units: list[str], overlap_tokens: int) -> tuple[list[str], int]:
    """Seed the next chunk with trailing units so adjacent chunks share context."""
    carried: list[str] = []
    tokens = 0
    for unit in reversed(units):
        unit_tokens = count_tokens(unit)
        if tokens + unit_tokens > overlap_tokens:
            break
        carried.insert(0, unit)
        tokens += unit_tokens
    return carried, tokens


def _make_chunk(index: int, units: list[str]) -> TextChunk:
    content = "\n\n".join(units)
    return TextChunk(index=index, content=content, token_count=count_tokens(content))


def chunk_text(text: str, *, max_tokens: int = 512, overlap_tokens: int = 64) -> list[TextChunk]:
    paragraphs = _split_paragraphs(text)

    # Normalize so no single unit exceeds the budget (rare giant paragraphs).
    units: list[str] = []
    for paragraph in paragraphs:
        if count_tokens(paragraph) <= max_tokens:
            units.append(paragraph)
        else:
            units.extend(_split_long_paragraph(paragraph, max_tokens))

    chunks: list[TextChunk] = []
    current: list[str] = []
    current_tokens = 0
    for unit in units:
        unit_tokens = count_tokens(unit)
        if current and current_tokens + unit_tokens > max_tokens:
            chunks.append(_make_chunk(len(chunks), current))
            current, current_tokens = _carry_overlap(current, overlap_tokens)
        current.append(unit)
        current_tokens += unit_tokens

    if current:
        chunks.append(_make_chunk(len(chunks), current))
    return chunks
