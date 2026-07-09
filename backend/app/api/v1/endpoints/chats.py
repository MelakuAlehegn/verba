from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.core.sse import format_sse
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatRead, ChatSourcesUpdate, ChatUpdate
from app.schemas.document import DocumentRead
from app.schemas.message import MessageCreate, MessagePair, MessageRead
from app.services.chat_document_service import (
    UnknownDocumentError,
    list_chat_sources,
    resolve_chat_scope,
    set_chat_sources,
)
from app.services.chat_service import (
    create_chat_for_user,
    delete_chat_for_user,
    get_chat_for_user,
    list_chats_for_user,
    update_chat_for_user,
)
from app.services.message_service import (
    list_messages_for_chat,
    post_message_to_chat,
    recent_history,
    start_message_turn,
    start_regeneration,
    stream_message_reply,
)
from app.services.rag.embedding import Embedder, get_embedder
from app.services.rag.llm import LLMProvider, get_llm_provider
from app.services.rag.vector_store import VectorStore, get_vector_store

router = APIRouter(prefix="/chats", tags=["chats"])


def get_owned_chat(
    chat_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Chat:
    """Resolve a chat the current user owns, or 404.

    Returning 404 (not 403) for someone else's chat keeps a chat's existence
    private across tenants.
    """
    chat = get_chat_for_user(db, current_user, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.get("", response_model=list[ChatRead])
def list_chats_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatRead]:
    chats = list_chats_for_user(db, current_user)
    return [ChatRead.model_validate(chat) for chat in chats]


@router.post("", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
def create_chat_endpoint(
    payload: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatRead:
    chat = create_chat_for_user(db, current_user, payload)
    return ChatRead.model_validate(chat)


@router.get("/{chat_id}", response_model=ChatRead)
def get_chat_endpoint(chat: Chat = Depends(get_owned_chat)) -> ChatRead:
    return ChatRead.model_validate(chat)


@router.patch("/{chat_id}", response_model=ChatRead)
def update_chat_endpoint(
    payload: ChatUpdate,
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
) -> ChatRead:
    updated = update_chat_for_user(db, chat, payload)
    return ChatRead.model_validate(updated)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_endpoint(
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
) -> None:
    delete_chat_for_user(db, chat)


@router.get("/{chat_id}/documents", response_model=list[DocumentRead])
def list_chat_sources_endpoint(
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    sources = list_chat_sources(db, chat)
    return [DocumentRead.model_validate(document) for document in sources]


@router.put("/{chat_id}/documents", response_model=list[DocumentRead])
def set_chat_sources_endpoint(
    payload: ChatSourcesUpdate,
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    try:
        sources = set_chat_sources(db, chat, payload.document_ids)
    except UnknownDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more documents don't belong to you.",
        ) from exc
    return [DocumentRead.model_validate(document) for document in sources]


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
def list_messages_endpoint(
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[MessageRead]:
    messages = list_messages_for_chat(db, chat, limit=limit, offset=offset)
    return [MessageRead.model_validate(message) for message in messages]


@router.post(
    "/{chat_id}/messages",
    response_model=MessagePair,
    status_code=status.HTTP_201_CREATED,
)
def post_message_endpoint(
    payload: MessageCreate,
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    vector_store: VectorStore = Depends(get_vector_store),
    llm: LLMProvider = Depends(get_llm_provider),
) -> MessagePair:
    user_message, assistant_message = post_message_to_chat(
        db, chat, payload, embedder=embedder, vector_store=vector_store, llm=llm
    )
    return MessagePair(
        user_message=MessageRead.model_validate(user_message),
        assistant_message=MessageRead.model_validate(assistant_message),
    )


def _answer_stream_response(
    *,
    user_id: UUID,
    chat_id: str,
    assistant_id: UUID,
    query: str,
    history: list[tuple[str, str]],
    document_ids: list[UUID] | None,
    embedder: Embedder,
    vector_store: VectorStore,
    llm: LLMProvider,
) -> StreamingResponse:
    """Stream an assistant answer over SSE. Shared by the send and regenerate
    endpoints — the assistant row is already open in 'streaming' state."""

    def event_stream() -> Iterator[str]:
        # The generator owns its own DB session: it outlives the request's
        # session and does live writes (token accumulation → final persist).
        gen_db = SessionLocal()
        replies = stream_message_reply(
            gen_db,
            user_id=user_id,
            query=query,
            assistant_message_id=assistant_id,
            embedder=embedder,
            vector_store=vector_store,
            llm=llm,
            history=history,
            document_ids=document_ids,
        )
        try:
            # Drain tokens; the generator returns the citation summary on finish.
            citations: list[dict[str, object]] = []
            while True:
                try:
                    yield format_sse({"delta": next(replies)})
                except StopIteration as finished:
                    citations = finished.value or []
                    break
            yield format_sse(
                {"chat_id": chat_id, "message_id": str(assistant_id), "citations": citations},
                event="done",
            )
        except Exception:
            # stream_message_reply persisted status=failed in its own finally.
            yield format_sse({"message": "Generation failed"}, event="error")
        finally:
            # If the client disconnected mid-stream, closing the inner generator
            # raises GeneratorExit inside it → it persists the partial as
            # 'stopped' (never leaving the row stuck at 'streaming').
            close = getattr(replies, "close", None)
            if close is not None:
                close()
            gen_db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{chat_id}/messages/stream")
def stream_message_endpoint(
    payload: MessageCreate,
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    vector_store: VectorStore = Depends(get_vector_store),
    llm: LLMProvider = Depends(get_llm_provider),
) -> StreamingResponse:
    # Capture history + scope before persisting this turn, then open the user
    # turn + an empty 'streaming' assistant row for the generator to fill.
    history = recent_history(db, chat.id)
    document_ids = resolve_chat_scope(db, chat)
    _, assistant_message = start_message_turn(db, chat, payload.content)
    return _answer_stream_response(
        user_id=chat.user_id,
        chat_id=str(chat.id),
        assistant_id=assistant_message.id,
        query=payload.content,
        history=history,
        document_ids=document_ids,
        embedder=embedder,
        vector_store=vector_store,
        llm=llm,
    )


@router.post("/{chat_id}/messages/regenerate")
def regenerate_message_endpoint(
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    vector_store: VectorStore = Depends(get_vector_store),
    llm: LLMProvider = Depends(get_llm_provider),
) -> StreamingResponse:
    # Drop the last assistant turn and re-answer the same question.
    context = start_regeneration(db, chat)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to regenerate."
        )
    return _answer_stream_response(
        user_id=chat.user_id,
        chat_id=str(chat.id),
        assistant_id=context.assistant_message_id,
        query=context.query,
        history=context.history,
        document_ids=context.document_ids,
        embedder=embedder,
        vector_store=vector_store,
        llm=llm,
    )
