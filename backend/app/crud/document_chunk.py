from __future__ import annotations

from collections.abc import Iterable, Sequence
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def get_chunks_by_ids(
    db: Session, chunk_ids: Sequence[UUID], user_id: UUID
) -> Sequence[DocumentChunk]:
    # Tenant-scoped: even though Qdrant already filtered by user_id, we filter
    # again here so a chunk can never cross tenants (defense in depth).
    #
    # We also drop chunks whose parent document is soft-deleted: a stray Qdrant
    # point left by an incomplete delete (e.g. a pre-fix deletion) can otherwise
    # inject content from a document the user removed. Joining to `documents` and
    # requiring deleted_at IS NULL makes that impossible — the match is treated
    # as store drift and skipped.
    if not chunk_ids:
        return []
    return db.scalars(
        select(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            DocumentChunk.id.in_(chunk_ids),
            DocumentChunk.user_id == user_id,
            Document.deleted_at.is_(None),
        )
    ).all()


def search_chunks_by_keyword(
    db: Session,
    *,
    user_id: UUID,
    query: str,
    document_ids: Iterable[UUID] | None = None,
    limit: int = 20,
) -> list[UUID]:
    """Lexical (full-text) search over chunk content, best-ranked first.

    The keyword half of hybrid retrieval: catches exact terms, IDs, and codes
    that embeddings blur. Tenant- and (optionally) document-scoped, and skips
    soft-deleted documents — same guarantees as the vector path.
    """
    if not query.strip():
        return []
    tsquery = func.plainto_tsquery("english", query)
    rank = func.ts_rank(DocumentChunk.content_tsv, tsquery)
    conditions = [
        DocumentChunk.user_id == user_id,
        Document.deleted_at.is_(None),
        DocumentChunk.content_tsv.op("@@")(tsquery),
    ]
    if document_ids is not None:
        conditions.append(DocumentChunk.document_id.in_(list(document_ids)))
    rows = db.execute(
        select(DocumentChunk.id)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(*conditions)
        .order_by(rank.desc())
        .limit(limit)
    ).all()
    return [row[0] for row in rows]


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
