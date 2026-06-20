"""Inspect how a document gets chunked — the RAG chunking learning lab.

Usage (from backend/, with the venv active):
    python scripts/inspect_chunking.py path/to/file.md
    cat file.txt | python scripts/inspect_chunking.py

Reads text, runs the chunker with the config defaults, and prints each chunk's
index, token count, and a preview so you can see the boundaries and overlap.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.core.config import get_settings
from app.services.rag.chunking import chunk_text


def main() -> None:
    settings = get_settings()
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    chunks = chunk_text(
        text,
        max_tokens=settings.chunk_max_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )

    print(f"max_tokens={settings.chunk_max_tokens} overlap={settings.chunk_overlap_tokens}")
    print(f"total tokens={len(text.split())} -> {len(chunks)} chunks\n")
    for chunk in chunks:
        preview = " ".join(chunk.content.split())[:140]
        print(f"[{chunk.index}] tokens={chunk.token_count:<5} {preview}...")


if __name__ == "__main__":
    main()
