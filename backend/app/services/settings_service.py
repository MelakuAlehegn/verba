from __future__ import annotations

from sqlalchemy.orm import Session

from app.crud.user_setting import create_user_settings, get_user_settings, update_user_settings
from app.models.user import User
from app.models.user_setting import UserSetting
from app.schemas.settings import SettingsUpdate


def get_or_create_user_settings_for_user(db: Session, user: User) -> UserSetting:
    user_settings = get_user_settings(db, user.id)
    if user_settings is None:
        user_settings = create_user_settings(db, user_id=user.id)
        db.commit()
        db.refresh(user_settings)
    return user_settings


def update_user_settings_for_user(
    db: Session,
    user: User,
    payload: SettingsUpdate,
) -> UserSetting:
    user_settings = get_or_create_user_settings_for_user(db, user)
    update_user_settings(db, user_settings, **payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user_settings)
    return user_settings

