from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.settings_service import (
    get_or_create_user_settings_for_user,
    update_user_settings_for_user,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
def read_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SettingsRead:
    user_settings = get_or_create_user_settings_for_user(db, current_user)
    return SettingsRead.model_validate(user_settings)


@router.patch("", response_model=SettingsRead)
def patch_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SettingsRead:
    user_settings = update_user_settings_for_user(db, current_user, payload)
    return SettingsRead.model_validate(user_settings)

