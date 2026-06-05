from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_setting import UserSetting


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def create_user(
    db: Session,
    *,
    email: str,
    name: str | None = None,
    avatar_url: str | None = None,
) -> User:
    user = User(email=email, name=name, avatar_url=avatar_url, last_login_at=datetime.now(timezone.utc))
    db.add(user)
    db.flush()
    return user


def update_user_profile(
    db: Session,
    user: User,
    *,
    name: str | None = None,
    avatar_url: str | None = None,
) -> User:
    if name is not None:
        user.name = name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    db.flush()
    return user


def touch_user_last_login(db: Session, user: User) -> User:
    user.last_login_at = datetime.now(timezone.utc)
    db.flush()
    return user


def create_default_user_settings(db: Session, user_id: UUID) -> UserSetting:
    settings = UserSetting(user_id=user_id)
    db.add(settings)
    db.flush()
    return settings
