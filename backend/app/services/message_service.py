from __future__ import annotations

from collections.abc import Iterator, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud.chat import touch_chat
from app.crud.message import (
    create_message,
    get_message_by_id,
    list_messages,
    set_message_content,
)
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.message import MessageCreate
from app.services.rag.embedding import Embedder
from app.services.rag.generation import build_prompt
from app.services.rag.llm import LLMProvider
from app.services.rag.retrieval import retrieve_context
from app.services.rag.vector_store import VectorStore


def list_messages_for_chat(
    db: Session,
    chat: Chat,
    *,
    limit: int,
    offset: int,
) -> Sequence[Message]:
    return list_messages(db, chat.id, limit=limit, offset=offset)


def _answer(
    db: Session,
    *,
    user_id: UUID,
    query: str,
    embedder: Embedder,
    vector_store: VectorStore,
    llm: LLMProvider,
) -> Iterator[str]:
    """Retrieve context for the query and stream the grounded answer.

    document_ids=None searches across all the user's vectors — i.e. every
    ingested ('ready') document. Per-chat scoping is a later slice.
    """
    settings = get_settings()
    chunks = retrieve_context(
        db,
        user_id=user_id,
        query=query,
        embedder=embedder,
        vector_store=vector_store,
        document_ids=None,
        limit=settings.retrieval_top_k,
    )
    yield from llm.stream(build_prompt(query, chunks))


def post_message_to_chat(
    db: Session,
    chat: Chat,
    payload: MessageCreate,
    *,
    embedder: Embedder,
    vector_store: VectorStore,
    llm: LLMProvider,
) -> tuple[Message, Message]:
    """Non-streaming turn: persist the user message, generate the full answer,
    persist the assistant message. Used by the JSON endpoint."""
    settings = get_settings()
    user_message = create_message(
        db, chat_id=chat.id, user_id=chat.user_id, role="user", content=payload.content
    )
    answer = "".join(
        _answer(
            db,
            user_id=chat.user_id,
            query=payload.content,
            embedder=embedder,
            vector_store=vector_store,
            llm=llm,
        )
    )
    assistant_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="assistant",
        content=answer,
        model=settings.generation_model,
    )
    touch_chat(db, chat)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message


def start_message_turn(db: Session, chat: Chat, content: str) -> tuple[Message, Message]:
    """Persist the user message and an empty assistant message in 'streaming'
    state, returning both so the SSE endpoint can fill the assistant live."""
    settings = get_settings()
    user_message = create_message(
        db, chat_id=chat.id, user_id=chat.user_id, role="user", content=content
    )
    assistant_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="assistant",
        content="",
        status="streaming",
        model=settings.generation_model,
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
) -> Iterator[str]:
    """Yield answer tokens (for SSE), accumulate them, and persist the finished
    assistant message as 'complete' once the stream ends."""
    parts: list[str] = []
    for token in _answer(
        db,
        user_id=user_id,
        query=query,
        embedder=embedder,
        vector_store=vector_store,
        llm=llm,
    ):
        parts.append(token)
        yield token
    finalize_assistant_message(db, assistant_message_id, content="".join(parts), status="complete")


def finalize_assistant_message(
    db: Session, message_id: UUID, *, content: str, status: str
) -> None:
    message = get_message_by_id(db, message_id)
    if message is not None:
        set_message_content(db, message, content=content, status=status)
        db.commit()
