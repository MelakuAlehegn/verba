from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    onboarded_at: datetime | None = None
    last_login_at: datetime | None = None

