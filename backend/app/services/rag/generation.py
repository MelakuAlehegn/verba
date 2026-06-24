"""Build the grounded prompt that turns retrieved chunks into an answer.

Kept separate from the LLM provider: this is RAG logic (how we instruct the
model and present context), independent of which model runs it.
"""

from __future__ import annotations

from app.services.rag.retrieval import RetrievedChunk

# Passed as the model's system instruction (weighted more heavily than inline
# text). Deliberately strict: Verba is document Q&A, not a general chatbot.
SYSTEM_INSTRUCTION = (
    "You are Verba, an assistant that answers strictly from the user's own documents.\n"
    "Rules:\n"
    "1. Use ONLY the provided context. Never use prior or general knowledge.\n"
    "2. Answer only if the context directly answers the question. If it does not — "
    "including when it merely mentions a related term in passing — do not attempt an "
    'answer. Reply plainly, e.g. "I couldn\'t find anything about that in your '
    'documents." Do not explain what the documents happen to mention instead.\n'
    "3. Never invent facts or sources, and never answer off-topic or general-knowledge "
    "questions.\n"
    "4. Cite sources as [Source N], using only the numbered sources in the context and "
    "only those you actually used.\n"
    "5. Be concise."
)


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    if chunks:
        context = "\n\n".join(
            f"[Source {index}]\n{chunk.content}" for index, chunk in enumerate(chunks, start=1)
        )
    else:
        context = "(no relevant context found in the user's documents)"

    return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
