from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.chat import create_chat, delete_chat, get_chat, list_chats, update_chat
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatUpdate


def list_chats_for_user(db: Session, user: User) -> Sequence[Chat]:
    return list_chats(db, user.id)


def get_chat_for_user(db: Session, user: User, chat_id: UUID) -> Chat | None:
    return get_chat(db, chat_id, user.id)


def create_chat_for_user(db: Session, user: User, payload: ChatCreate) -> Chat:
    chat = create_chat(db, user_id=user.id, **payload.model_dump(exclude_none=True))
    db.commit()
    db.refresh(chat)
    return chat


def update_chat_for_user(db: Session, chat: Chat, payload: ChatUpdate) -> Chat:
    update_chat(db, chat, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(chat)
    return chat


def delete_chat_for_user(db: Session, chat: Chat) -> None:
    delete_chat(db, chat)
    db.commit()
