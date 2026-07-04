from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.chat_document import (
    get_scoped_documents,
    list_chat_document_ids,
    set_chat_documents,
)
from app.crud.document import list_documents
from app.models.chat import Chat
from app.models.document import Document


class UnknownDocumentError(ValueError):
    """A requested source id isn't one of the user's documents."""


def list_chat_sources(db: Session, chat: Chat) -> Sequence[Document]:
    return get_scoped_documents(db, chat.id, chat.user_id)


def set_chat_sources(
    db: Session, chat: Chat, document_ids: Sequence[UUID]
) -> Sequence[Document]:
    """Replace the chat's sources with `document_ids`, after checking every id
    belongs to the user (and isn't deleted). Returns the resolved sources."""
    requested = list(dict.fromkeys(document_ids))  # de-dupe, keep order
    owned = {document.id for document in list_documents(db, chat.user_id)}
    unknown = [document_id for document_id in requested if document_id not in owned]
    if unknown:
        raise UnknownDocumentError(str(unknown[0]))

    set_chat_documents(db, chat_id=chat.id, user_id=chat.user_id, document_ids=requested)
    db.commit()
    return get_scoped_documents(db, chat.id, chat.user_id)


def resolve_chat_scope(db: Session, chat: Chat) -> list[UUID] | None:
    """Document ids to retrieve against for this chat.

    None  → the chat has no attached sources (unscoped): search all the user's
            documents (legacy behavior for pre-scoping chats).
    list  → search only these (may be empty if every source was since deleted,
            which correctly yields no context).
    """
    if not list_chat_document_ids(db, chat.id):
        return None
    return [document.id for document in get_scoped_documents(db, chat.id, chat.user_id)]
