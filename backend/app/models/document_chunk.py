from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.chunk_embedding import ChunkEmbedding
    from app.models.document import Document


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        # A document can't have two chunks at the same position.
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_doc_index"),
        # GIN index over the full-text column powers keyword (hybrid) search.
        Index("ix_document_chunks_content_tsv", "content_tsv", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalized from the document for fast tenant filtering at retrieval time.
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # `metadata` is reserved by SQLAlchemy's declarative Base, so the Python
    # attribute is renamed while the DB column stays "metadata".
    chunk_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    chunking_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Postgres-maintained full-text vector of `content`, for keyword search. A
    # generated column stays in sync automatically — no app writes, no trigger.
    content_tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="chunks")
    embeddings: Mapped[list[ChunkEmbedding]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
    )
