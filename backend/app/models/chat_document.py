from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ChatDocument(Base):
    """Which documents a chat is scoped to — its sources.

    Retrieval for a chat is filtered to these document_ids, so a conversation
    only searches the files the user attached to it. `user_id` is denormalized
    for tenant checks. A chat with no rows is treated as unscoped (falls back to
    all of the user's documents), which keeps pre-scoping chats working.
    """

    __tablename__ = "chat_documents"
    __table_args__ = (UniqueConstraint("chat_id", "document_id", name="uq_chat_document"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
