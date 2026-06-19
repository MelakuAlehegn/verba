from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import Chat


def get_chat(db: Session, chat_id: UUID, user_id: UUID) -> Chat | None:
    # Filter by user_id as well as id: a chat owned by another user must be
    # indistinguishable from one that does not exist (tenant isolation).
    return db.scalar(select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id))


def list_chats(db: Session, user_id: UUID) -> Sequence[Chat]:
    return db.scalars(
        select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc())
    ).all()


def create_chat(
    db: Session,
    *,
    user_id: UUID,
    title: str = "New chat",
    provider: str = "groq",
) -> Chat:
    chat = Chat(user_id=user_id, title=title, provider=provider)
    db.add(chat)
    db.flush()
    return chat


def update_chat(
    db: Session,
    chat: Chat,
    *,
    title: str | None = None,
    provider: str | None = None,
) -> Chat:
    if title is not None:
        chat.title = title
    if provider is not None:
        chat.provider = provider
    db.flush()
    return chat


def delete_chat(db: Session, chat: Chat) -> None:
    db.delete(chat)
    db.flush()


def touch_chat(db: Session, chat: Chat) -> Chat:
    # Bump updated_at so the chat surfaces at the top of the recency-ordered
    # session list after activity (e.g. a new message).
    chat.updated_at = datetime.now(UTC)
    db.flush()
    return chat
