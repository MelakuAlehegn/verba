from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.chat_document import ChatDocument
from app.models.document import Document


def list_chat_document_ids(db: Session, chat_id: UUID) -> list[UUID]:
    """Every document id attached to the chat (regardless of document state)."""
    return list(
        db.scalars(
            select(ChatDocument.document_id).where(ChatDocument.chat_id == chat_id)
        ).all()
    )


def get_scoped_documents(db: Session, chat_id: UUID, user_id: UUID) -> Sequence[Document]:
    """The chat's attached documents that still exist — the user's, not deleted
    (any status, so a still-processing source shows up). Used both to answer
    against the chat's sources and to render them in the UI. A doc without
    vectors yet simply contributes nothing to retrieval."""
    return db.scalars(
        select(Document)
        .join(ChatDocument, ChatDocument.document_id == Document.id)
        .where(
            ChatDocument.chat_id == chat_id,
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at)
    ).all()


def set_chat_documents(
    db: Session, *, chat_id: UUID, user_id: UUID, document_ids: Sequence[UUID]
) -> None:
    """Replace the chat's scope with exactly `document_ids`. Callers must have
    validated ownership first."""
    db.execute(delete(ChatDocument).where(ChatDocument.chat_id == chat_id))
    for document_id in document_ids:
        db.add(ChatDocument(chat_id=chat_id, document_id=document_id, user_id=user_id))
    db.flush()
