from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class CitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID | None
    chunk_id: UUID | None
    rank: int
    score: float | None
    quote_preview: str | None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: UUID
    role: str
    content: str
    status: str
    model: str | None
    token_usage: dict[str, object] | None
    created_at: datetime
    citations: list[CitationRead] = []


class MessagePair(BaseModel):
    """Both messages produced by a single POST: the user's turn and the reply."""

    user_message: MessageRead
    assistant_message: MessageRead
