from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.crud.chat import touch_chat
from app.crud.message import create_message, list_messages
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.message import MessageCreate

STUB_MODEL = "stub-echo"


def list_messages_for_chat(
    db: Session,
    chat: Chat,
    *,
    limit: int,
    offset: int,
) -> Sequence[Message]:
    return list_messages(db, chat.id, limit=limit, offset=offset)


def _generate_reply(content: str) -> str:
    # Placeholder until the RAG pipeline + LLM provider land (Phase 4). Real
    # retrieval + streaming will replace this function without changing callers.
    return f"(stub) You said: {content}"


def post_message_to_chat(
    db: Session,
    chat: Chat,
    payload: MessageCreate,
) -> tuple[Message, Message]:
    # user_id is denormalized onto every message for tenant filtering; the
    # assistant message carries the same owner, with role marking the author.
    user_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="user",
        content=payload.content,
    )
    assistant_message = create_message(
        db,
        chat_id=chat.id,
        user_id=chat.user_id,
        role="assistant",
        content=_generate_reply(payload.content),
        model=STUB_MODEL,
    )
    touch_chat(db, chat)

    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message
