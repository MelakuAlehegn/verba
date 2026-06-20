from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class ChunkEmbedding(Base):
    """Registry of which chunks are embedded, by which model/version, and where.

    Decouples embeddings from chunk text so the embedding model can change
    (a tracked, resumable re-index) without touching `document_chunks`.
    """

    __tablename__ = "chunk_embeddings"
    __table_args__ = (
        # One embedding per chunk per model+version; prevents duplicates.
        UniqueConstraint(
            "chunk_id", "embedding_model", "embedding_version", name="uq_chunk_embeddings_identity"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chunk_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_version: Mapped[str] = mapped_column(String(64), nullable=False)
    # Qdrant point id — equals chunk_id by convention.
    vector_id: Mapped[str] = mapped_column(String(64), nullable=False)
    # pending|indexed|failed — indexed for the reconciliation job's scans.
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    chunk: Mapped[DocumentChunk] = relationship(back_populates="embeddings")
