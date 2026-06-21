"""Build the grounded prompt that turns retrieved chunks into an answer.

Kept separate from the LLM provider: this is RAG logic (how we instruct the
model and present context), independent of which model runs it.
"""

from __future__ import annotations

from app.services.rag.retrieval import RetrievedChunk

_SYSTEM_INSTRUCTION = (
    "You are a helpful assistant that answers questions using ONLY the context "
    "below, which comes from the user's own documents. If the answer is not in "
    "the context, say you don't know rather than guessing. Cite the sources you "
    "use as [Source N]."
)


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    if chunks:
        context = "\n\n".join(
            f"[Source {index}]\n{chunk.content}" for index, chunk in enumerate(chunks, start=1)
        )
    else:
        context = "(no relevant context found in the user's documents)"

    return (
        f"{_SYSTEM_INSTRUCTION}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )
