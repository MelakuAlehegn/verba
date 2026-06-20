"""Sanity-check the embedder. WARNING: makes ONE real Gemini API call.

Run sparingly (free-tier rate limits). Usage, from backend/ with the venv:
    python scripts/inspect_embedding.py "some text to embed"
"""

from __future__ import annotations

import sys

from app.services.rag.embedding import get_embedder


def main() -> None:
    text = sys.argv[1] if len(sys.argv) > 1 else "hello world"
    embedder = get_embedder()
    vector = embedder.embed_query(text)

    norm = sum(component * component for component in vector) ** 0.5
    print(f"model={embedder.model} version={embedder.version} dim={embedder.dimension}")
    print(f"vector length={len(vector)} first5={[round(v, 4) for v in vector[:5]]}")
    print(f"L2 norm={norm:.4f} (≈1.0 means normalized)")


if __name__ == "__main__":
    main()
