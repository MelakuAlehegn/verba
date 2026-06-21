from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.message import Message


class MessageCitation(Base):
    """A source chunk behind an assistant answer.

    First-class (not JSONB on the message) so citations are queryable and
    survive document deletion: document_id/chunk_id are SET NULL on delete,
    leaving the preview text as a "source no longer available" record.
    """

    __tablename__ = "message_citations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    chunk_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quote_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    message: Mapped[Message] = relationship(back_populates="citations")
