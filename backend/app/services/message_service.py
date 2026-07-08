from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud.chat import touch_chat
from app.crud.message import (
    create_message,
    get_message_by_id,
    get_recent_messages,
    list_messages,
    set_message_content,
)
from app.crud.message_citation import create_message_citation
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.message import MessageCreate
from app.services.chat_document_service import resolve_chat_scope
from app.services.rag.embedding import Embedder
from app.services.rag.generation import SYSTEM_INSTRUCTION, build_prompt
from app.services.rag.llm import LLMProvider
from app.services.rag.query_rewriting import rewrite_query
from app.services.rag.retrieval import RetrievedChunk, retrieve_context
from app.services.rag.vector_store import VectorStore

_QUOTE_PREVIEW_CHARS = 200


def list_messages_for_chat(
    db: Session,
    chat: Chat,
    *,
    limit: int,
    offset: int,
) -> Sequence[Message]:
    return list_messages(db, chat.id, limit=limit, offset=offset)


def recent_history(db: Session, chat_id: UUID) -> list[tuple[str, str]]:
    """Recent conversation as `(role, content)`, oldest-first, for the query
    rewriter. Call this *before* persisting the current turn. Empty-content rows
    (e.g. an in-flight streaming assistant placeholder) are skipped."""
    settings = get_settings()
    rows = get_recent_messages(db, chat_id, limit=settings.query_rewrite_history_messages)
    return [(row.role, row.content) for row in rows if row.content and row.content.strip()]


def _retrieve_and_prompt(
    db: Session,
    *,
    user_id: UUID,
    query: str,
    history: Sequence[tuple[str, str]],
    document_ids: Sequence[UUID] | None,
    embedder: Embedder,
    vector_store: VectorStore,
    llm: LLMProvider,
) -> tuple[list[RetrievedChunk], str]:
    # Rewrite follow-ups into a standalone query so both retrieval *and*
    # generation see resolved references. Used for both; the user's raw message
    # is still what we persist and display.
    settings = get_settings()
    search_query = (
        rewrite_query(query, history, llm=llm) if settings.query_rewrite_enabled else query
    )
    memory = history if settings.conversation_memory_enabled else ()
    # document_ids scopes retrieval to the chat's sources; None means the chat is
    # unscoped, so search all of the user's documents.
    chunks = retrieve_context(
        db,
        user_id=user_id,
        query=search_query,
        embedder=embedder,
        vector_store=vector_store,
        document_ids=document_ids,
        limit=settings.retrieval_top_k,
        min_score=settings.retrieval_score_threshold,
        candidate_pool=settings.rerank_candidate_pool,
        mmr_lambda=settings.mmr_lambda,
        hybrid=settings.hybrid_search_enabled,
    )
    return chunks, build_prompt(search_query, chunks, history=memory)


def _persist_citations(db: Session, message_id: UUID, chunks: list[RetrievedChunk]) -> None:
    for rank, chunk in enumerate(chunks, start=1):
        create_message_citation(
            db,
            message_id=message_id,
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            rank=rank,
            score=chunk.score,
            quote_preview=chunk.content[:_QUOTE_PREVIEW_CHARS],
        )


def _citation_summaries(chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
    return [
        {
            "rank": rank,
            "document_id": str(chunk.document_id),
            "chunk_id": str(chunk.chunk_id),
            "score": chunk.score,
        }
        for rank, chunk in enumerate(chunks, start=1)
    ]


def post_message_to_chat(
    db: Session,
    chat: Chat,
    payload: MessageCreate,
    *,
    embedder: Embedder,
    vector_store: VectorStore,
    llm: LLMProvider,
) -> tuple[Message, Message]:
    """Non-streaming turn: persist user message, generate the full answer,
    persist the assistant message + its citations. Used by the JSON endpoint."""
    settings = get_settings()
    # Capture history before persisting this turn, so the rewriter sees only
    # prior conversation (not the question it's rewriting).
    history = recent_history(db, chat.id)
    document_ids = resolve_chat_scope(db, chat)
    user_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="user",
        content=payload.content,
        created_at=datetime.now(UTC),
    )
    chunks, prompt = _retrieve_and_prompt(
        db,
        user_id=chat.user_id,
        query=payload.content,
        history=history,
        document_ids=document_ids,
        embedder=embedder,
        vector_store=vector_store,
        llm=llm,
    )
    answer = "".join(llm.stream(prompt, system=SYSTEM_INSTRUCTION))
    assistant_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="assistant",
        content=answer,
        model=settings.generation_model,
        created_at=datetime.now(UTC),
    )
    _persist_citations(db, assistant_message.id, chunks)
    touch_chat(db, chat)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message


def start_message_turn(db: Session, chat: Chat, content: str) -> tuple[Message, Message]:
    """Persist the user message and an empty 'streaming' assistant message so
    the SSE endpoint can fill it live."""
    settings = get_settings()
    now = datetime.now(UTC)
    user_message = create_message(
        db, chat_id=chat.id, user_id=chat.user_id, role="user", content=content, created_at=now
    )
    assistant_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="assistant",
        content="",
        status="streaming",
        model=settings.generation_model,
        # Strictly after the user message so history can't render answer-before-question
        # (both rows otherwise share the transaction's now() timestamp).
        created_at=now + timedelta(milliseconds=1),
    )
    touch_chat(db, chat)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message


def stream_message_reply(
    db: Session,
    *,
    user_id: UUID,
    query: str,
    assistant_message_id: UUID,
    embedder: Embedder,
    vector_store: VectorStore,
    llm: LLMProvider,
    history: Sequence[tuple[str, str]] = (),
    document_ids: Sequence[UUID] | None = None,
) -> Iterator[str]:
    """Yield answer tokens (for SSE), persist the finished message + citations,
    and return the citation summary as the generator's return value (so the
    endpoint can put it in the terminal 'done' event)."""
    chunks, prompt = _retrieve_and_prompt(
        db,
        user_id=user_id,
        query=query,
        history=history,
        document_ids=document_ids,
        embedder=embedder,
        vector_store=vector_store,
        llm=llm,
    )
    parts: list[str] = []
    for token in llm.stream(prompt, system=SYSTEM_INSTRUCTION):
        parts.append(token)
        yield token
    finalize_assistant_message(
        db, assistant_message_id, content="".join(parts), status="complete", chunks=chunks
    )
    return _citation_summaries(chunks)


def finalize_assistant_message(
    db: Session,
    message_id: UUID,
    *,
    content: str,
    status: str,
    chunks: list[RetrievedChunk] | None = None,
) -> None:
    message = get_message_by_id(db, message_id)
    if message is None:
        return
    set_message_content(db, message, content=content, status=status)
    if chunks:
        _persist_citations(db, message_id, chunks)
    db.commit()
