from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def get_document(db: Session, document_id: UUID, user_id: UUID) -> Document | None:
    # Tenant-scoped, and hides soft-deleted rows.
    return db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        )
    )


def get_document_by_id(db: Session, document_id: UUID) -> Document | None:
    # No tenant scope: the worker operates by document id, not on behalf of a user.
    return db.get(Document, document_id)


def mark_document_processing(db: Session, document: Document) -> Document:
    document.status = "processing"
    db.flush()
    return document


def mark_document_ready(db: Session, document: Document, *, chunk_count: int) -> Document:
    document.status = "ready"
    document.chunk_count = chunk_count
    document.processed_at = datetime.now(UTC)
    document.error_code = None
    document.error_message = None
    db.flush()
    return document


def mark_document_failed(
    db: Session, document: Document, *, error_code: str, error_message: str
) -> Document:
    document.status = "failed"
    document.error_code = error_code
    document.error_message = error_message
    db.flush()
    return document


def list_documents(db: Session, user_id: UUID) -> Sequence[Document]:
    return db.scalars(
        select(Document)
        .where(Document.user_id == user_id, Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
    ).all()


def create_document(
    db: Session,
    *,
    document_id: UUID,
    user_id: UUID,
    filename: str,
    mime_type: str,
    size_bytes: int,
    storage_key: str,
    checksum: str | None = None,
    status: str = "queued",
) -> Document:
    document = Document(
        id=document_id,
        user_id=user_id,
        filename=filename,
        mime_type=mime_type,
        size_bytes=size_bytes,
        storage_key=storage_key,
        checksum=checksum,
        status=status,
        uploaded_at=datetime.now(UTC),
    )
    db.add(document)
    db.flush()
    return document


def soft_delete_document(db: Session, document: Document) -> Document:
    document.deleted_at = datetime.now(UTC)
    document.status = "deleted"
    db.flush()
    return document
