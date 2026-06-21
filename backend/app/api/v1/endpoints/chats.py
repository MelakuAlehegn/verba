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
from app.schemas.chat import ChatCreate, ChatRead, ChatUpdate
from app.schemas.message import MessageCreate, MessagePair, MessageRead
from app.services.chat_service import (
    create_chat_for_user,
    delete_chat_for_user,
    get_chat_for_user,
    list_chats_for_user,
    update_chat_for_user,
)
from app.services.message_service import (
    finalize_assistant_message,
    list_messages_for_chat,
    post_message_to_chat,
    start_message_turn,
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


@router.post("/{chat_id}/messages/stream")
def stream_message_endpoint(
    payload: MessageCreate,
    chat: Chat = Depends(get_owned_chat),
    db: Session = Depends(get_db),
    embedder: Embedder = Depends(get_embedder),
    vector_store: VectorStore = Depends(get_vector_store),
    llm: LLMProvider = Depends(get_llm_provider),
) -> StreamingResponse:
    # Persist the user turn + an empty 'streaming' assistant row synchronously,
    # then capture ids into locals for the generator.
    _, assistant_message = start_message_turn(db, chat, payload.content)
    user_id = chat.user_id
    chat_id = str(chat.id)
    assistant_id = assistant_message.id
    query = payload.content

    def event_stream() -> Iterator[str]:
        # The generator owns its own DB session: it outlives the request's
        # session and does live writes (token accumulation → final persist).
        gen_db = SessionLocal()
        try:
            replies = stream_message_reply(
                gen_db,
                user_id=user_id,
                query=query,
                assistant_message_id=assistant_id,
                embedder=embedder,
                vector_store=vector_store,
                llm=llm,
            )
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
            finalize_assistant_message(gen_db, assistant_id, content="", status="failed")
            yield format_sse({"message": "Generation failed"}, event="error")
        finally:
            gen_db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
