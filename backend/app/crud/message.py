from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
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


def get_recent_messages(
    db: Session,
    chat_id: UUID,
    *,
    limit: int,
) -> Sequence[Message]:
    """The most recent `limit` messages, returned oldest-first (chronological).

    Used to give the query rewriter a short window of prior conversation.
    """
    rows = db.scalars(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    ).all()
    return list(reversed(rows))


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
    created_at: datetime | None = None,
) -> Message:
    # created_at defaults to the DB server_default (func.now()), but callers can
    # set it explicitly to keep user/assistant order deterministic — both rows
    # of a turn otherwise share the same transaction timestamp.
    message = Message(
        chat_id=chat_id,
        user_id=user_id,
        role=role,
        content=content,
        status=status,
        model=model,
        token_usage=token_usage,
        **({"created_at": created_at} if created_at is not None else {}),
    )
    db.add(message)
    db.flush()
    return message


def get_message_by_id(db: Session, message_id: UUID) -> Message | None:
    return db.get(Message, message_id)


def set_message_content(db: Session, message: Message, *, content: str, status: str) -> Message:
    message.content = content
    message.status = status
    db.flush()
    return message


def delete_message(db: Session, message: Message) -> None:
    # message_citations cascade via their FK (ondelete CASCADE).
    db.delete(message)
    db.flush()
