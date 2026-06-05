from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user_setting import UserSetting


def get_user_settings(db: Session, user_id: UUID) -> UserSetting | None:
    return db.get(UserSetting, user_id)


def create_user_settings(
    db: Session,
    *,
    user_id: UUID,
    default_provider: str = "groq",
    theme: str = "system",
    retrieval_settings: dict[str, object] | None = None,
    preferences: dict[str, object] | None = None,
) -> UserSetting:
    user_settings = UserSetting(
        user_id=user_id,
        default_provider=default_provider,
        theme=theme,
        retrieval_settings=retrieval_settings or {},
        preferences=preferences or {},
    )
    db.add(user_settings)
    db.flush()
    return user_settings


def update_user_settings(
    db: Session,
    user_settings: UserSetting,
    *,
    default_provider: str | None = None,
    theme: str | None = None,
    retrieval_settings: dict[str, object] | None = None,
    preferences: dict[str, object] | None = None,
) -> UserSetting:
    if default_provider is not None:
        user_settings.default_provider = default_provider
    if theme is not None:
        user_settings.theme = theme
    if retrieval_settings is not None:
        user_settings.retrieval_settings = retrieval_settings
    if preferences is not None:
        user_settings.preferences = preferences
    db.flush()
    return user_settings

