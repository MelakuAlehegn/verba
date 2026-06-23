from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    onboarded_at: datetime | None = None
    last_login_at: datetime | None = None


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=2048)
    # When true, stamp onboarded_at (once) to mark first-run onboarding complete.
    onboarded: bool | None = None

