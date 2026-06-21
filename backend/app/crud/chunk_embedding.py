from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chunk_embedding import ChunkEmbedding


def create_chunk_embedding(
    db: Session,
    *,
    chunk_id: UUID,
    document_id: UUID,
    user_id: UUID,
    embedding_model: str,
    embedding_version: str,
    vector_id: str,
    status: str = "indexed",
) -> ChunkEmbedding:
    embedding = ChunkEmbedding(
        chunk_id=chunk_id,
        document_id=document_id,
        user_id=user_id,
        embedding_model=embedding_model,
        embedding_version=embedding_version,
        vector_id=vector_id,
        status=status,
    )
    db.add(embedding)
    db.flush()
    return embedding
