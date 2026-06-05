from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    default_provider: str
    theme: str
    retrieval_settings: dict[str, object] = Field(default_factory=dict)
    preferences: dict[str, object] = Field(default_factory=dict)


class SettingsUpdate(BaseModel):
    default_provider: str | None = None
    theme: str | None = None
    retrieval_settings: dict[str, object] | None = None
    preferences: dict[str, object] | None = None

