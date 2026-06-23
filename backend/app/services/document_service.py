from __future__ import annotations

import hashlib
from collections.abc import Sequence
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.crud.document import (
    create_document,
    get_document,
    list_documents,
    soft_delete_document,
)
from app.crud.document_chunk import delete_chunks_for_document
from app.models.document import Document
from app.models.user import User
from app.services.rag.vector_store import VectorStore
from app.storage.base import StorageClient


def list_documents_for_user(db: Session, user: User) -> Sequence[Document]:
    return list_documents(db, user.id)


def get_document_for_user(db: Session, user: User, document_id: UUID) -> Document | None:
    return get_document(db, document_id, user.id)


def upload_document_for_user(
    db: Session,
    user: User,
    storage: StorageClient,
    *,
    filename: str,
    content_type: str,
    data: bytes,
) -> Document:
    document_id = uuid4()
    storage_key = f"users/{user.id}/documents/{document_id}/{filename}"
    checksum = hashlib.sha256(data).hexdigest()

    # Stage the row first, then upload. If the upload raises we never commit,
    # so the row rolls back — no DB row pointing at a missing file. (The two
    # stores aren't transactional; a commit failure after upload could orphan
    # a file, which the cleanup job handles later.)
    document = create_document(
        db,
        document_id=document_id,
        user_id=user.id,
        filename=filename,
        mime_type=content_type,
        size_bytes=len(data),
        storage_key=storage_key,
        checksum=checksum,
        status="queued",
    )
    storage.put_object(storage_key, data, content_type)
    db.commit()
    db.refresh(document)
    return document


def delete_document_for_user(
    db: Session,
    document: Document,
    storage: StorageClient,
    vector_store: VectorStore,
) -> None:
    # Remove the file, its vectors, and its chunks (cascades chunk_embeddings) so
    # a deleted document can never resurface in retrieval. The row is soft-deleted
    # (kept as a tombstone); message_citations to its chunks become "unavailable".
    storage.delete_object(document.storage_key)
    vector_store.delete_document(document.id)
    delete_chunks_for_document(db, document.id)
    soft_delete_document(db, document)
    db.commit()
