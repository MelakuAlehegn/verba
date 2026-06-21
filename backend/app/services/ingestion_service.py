"""Orchestrates document ingestion: parse → chunk → embed → store.

This is the heart of the pipeline, kept free of Celery so it can be unit-tested
with fakes. The Celery task is a thin wrapper that supplies real dependencies
(storage, embedder, vector store) and its own DB session.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.crud.chunk_embedding import create_chunk_embedding
from app.crud.document import (
    get_document_by_id,
    mark_document_failed,
    mark_document_processing,
    mark_document_ready,
)
from app.crud.document_chunk import create_document_chunk, delete_chunks_for_document
from app.services.rag.chunking import CHUNKING_VERSION, chunk_text
from app.services.rag.embedding import Embedder
from app.services.rag.parsing import extract_text
from app.services.rag.vector_store import VectorPoint, VectorStore
from app.storage.base import StorageClient

logger = logging.getLogger(__name__)


def ingest_document(
    db: Session,
    document_id: UUID,
    *,
    storage: StorageClient,
    embedder: Embedder,
    vector_store: VectorStore,
) -> None:
    document = get_document_by_id(db, document_id)
    if document is None:
        logger.warning("ingest: document %s not found", document_id)
        return
    if document.status == "ready":
        return  # idempotent: already processed

    mark_document_processing(db, document)
    db.commit()

    try:
        settings = get_settings()
        data = storage.get_object(document.storage_key)
        text = extract_text(data, filename=document.filename)
        chunks = chunk_text(
            text,
            max_tokens=settings.chunk_max_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
        if not chunks:
            raise ValueError("Document produced no chunks")

        vectors = embedder.embed_documents([chunk.content for chunk in chunks])

        # Clear any prior run's data so a re-index doesn't duplicate or leave
        # stale vectors behind (Postgres rows here, Qdrant points below).
        vector_store.ensure_collection()
        vector_store.delete_document(document.id)
        delete_chunks_for_document(db, document.id)

        points: list[VectorPoint] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk_row = create_document_chunk(
                db,
                document_id=document.id,
                user_id=document.user_id,
                chunk_index=chunk.index,
                content=chunk.content,
                token_count=chunk.token_count,
                chunk_metadata=chunk.metadata,
                chunking_version=CHUNKING_VERSION,
            )
            create_chunk_embedding(
                db,
                chunk_id=chunk_row.id,
                document_id=document.id,
                user_id=document.user_id,
                embedding_model=embedder.model,
                embedding_version=embedder.version,
                vector_id=str(chunk_row.id),  # point id == chunk id by convention
                status="indexed",
            )
            points.append(
                VectorPoint(
                    chunk_id=chunk_row.id,
                    document_id=document.id,
                    user_id=document.user_id,
                    vector=vector,
                )
            )

        vector_store.upsert(points)
        mark_document_ready(db, document, chunk_count=len(chunks))
        db.commit()
        logger.info("ingest: document %s ready with %d chunks", document_id, len(chunks))
    except Exception as exc:
        # Roll back the partial chunk/embedding inserts, then record the failure
        # on the document in a fresh transaction so the UI can show a reason.
        db.rollback()
        document = get_document_by_id(db, document_id)
        if document is not None:
            mark_document_failed(
                db, document, error_code="ingestion_error", error_message=str(exc)[:500]
            )
            db.commit()
        logger.exception("ingest: failed for document %s", document_id)
