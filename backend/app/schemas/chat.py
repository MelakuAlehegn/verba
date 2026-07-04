from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, max_length=32)


class ChatUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, max_length=32)


class ChatSourcesUpdate(BaseModel):
    document_ids: list[UUID] = Field(default_factory=list)


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    provider: str
    pinned_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
