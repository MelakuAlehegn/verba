"""Rewrite a follow-up question into a standalone one before retrieval.

Retrieval embeds the user's message as-is, so a follow-up like "summarise that"
or "what about section 5?" carries no meaning on its own — the referent lives in
earlier turns. Embedding it finds nothing useful, and the generator is just as
lost. This module asks the LLM to fold the recent conversation back into the
question, producing a self-contained query we use for *both* retrieval and
generation.

Cost-aware: the first turn of a chat has no history, so we skip the call
entirely and return the question unchanged.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from app.services.rag.llm import LLMProvider

logger = logging.getLogger(__name__)

REWRITE_SYSTEM = (
    "You rewrite the user's latest message into a standalone search query, "
    'resolving pronouns and references ("it", "that", "the section") using the '
    "conversation above. If the message is already self-contained, return it "
    "unchanged. Reply with ONLY the rewritten query — no preamble, no quotes."
)


def rewrite_query(
    query: str,
    history: Sequence[tuple[str, str]],
    *,
    llm: LLMProvider,
) -> str:
    """Return a standalone version of `query` given `(role, content)` history.

    No history → returns `query` unchanged (and makes no LLM call). If the
    rewrite fails for any reason, we fall back to the original query rather than
    break answering.
    """
    if not history:
        return query

    conversation = "\n".join(f"{role.capitalize()}: {content}" for role, content in history)
    prompt = f"Conversation:\n{conversation}\n\nLatest message: {query}\n\nStandalone query:"
    try:
        rewritten = "".join(llm.stream(prompt, system=REWRITE_SYSTEM)).strip().strip('"').strip()
    except Exception:
        logger.warning("query rewrite failed; using original query", exc_info=True)
        return query

    result = rewritten or query
    logger.info("query rewrite: %r -> %r", query, result)
    return result
