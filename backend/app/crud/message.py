from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message


def list_messages(
    db: Session,
    chat_id: UUID,
    *,
    limit: int,
    offset: int,
) -> Sequence[Message]:
    return db.scalars(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at, Message.id)
        .limit(limit)
        .offset(offset)
    ).all()


def create_message(
    db: Session,
    *,
    chat_id: UUID,
    user_id: UUID,
    role: str,
    content: str,
    status: str = "complete",
    model: str | None = None,
    token_usage: dict[str, object] | None = None,
) -> Message:
    message = Message(
        chat_id=chat_id,
        user_id=user_id,
        role=role,
        content=content,
        status=status,
        model=model,
        token_usage=token_usage,
    )
    db.add(message)
    db.flush()
    return message
