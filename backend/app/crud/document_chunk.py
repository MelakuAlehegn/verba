from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


def get_chunks_by_ids(
    db: Session, chunk_ids: Sequence[UUID], user_id: UUID
) -> Sequence[DocumentChunk]:
    # Tenant-scoped: even though Qdrant already filtered by user_id, we filter
    # again here so a chunk can never cross tenants (defense in depth).
    if not chunk_ids:
        return []
    return db.scalars(
        select(DocumentChunk).where(
            DocumentChunk.id.in_(chunk_ids),
            DocumentChunk.user_id == user_id,
        )
    ).all()


def create_document_chunk(
    db: Session,
    *,
    document_id: UUID,
    user_id: UUID,
    chunk_index: int,
    content: str,
    token_count: int | None = None,
    chunk_metadata: dict[str, object] | None = None,
    chunking_version: str | None = None,
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document_id,
        user_id=user_id,
        chunk_index=chunk_index,
        content=content,
        token_count=token_count,
        chunk_metadata=chunk_metadata or {},
        chunking_version=chunking_version,
    )
    db.add(chunk)
    db.flush()
    return chunk


def delete_chunks_for_document(db: Session, document_id: UUID) -> None:
    # Used before re-processing so a re-index doesn't duplicate chunks.
    # Cascades to chunk_embeddings via the FK.
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    db.flush()
