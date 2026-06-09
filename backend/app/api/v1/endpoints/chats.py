from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatRead, ChatUpdate
from app.services.chat_service import (
    create_chat_for_user,
    delete_chat_for_user,
    get_chat_for_user,
    list_chats_for_user,
    update_chat_for_user,
)

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
