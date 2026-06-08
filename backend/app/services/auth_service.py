from __future__ import annotations

from sqlalchemy.orm import Session

from app.crud.oauth_account import create_oauth_account, get_oauth_account
from app.crud.user import (
    create_default_user_settings,
    create_user,
    get_user_by_email,
    touch_user_last_login,
    update_user_profile,
)
from app.models.user import User
from app.schemas.auth import OAuthProfile


def upsert_user_from_oauth_profile(db: Session, profile: OAuthProfile) -> User:
    oauth_account = get_oauth_account(
        db,
        provider=profile.provider,
        provider_account_id=profile.provider_account_id,
    )

    if oauth_account is not None:
        user = oauth_account.user
        update_user_profile(db, user, name=profile.name, avatar_url=profile.avatar_url)
        touch_user_last_login(db, user)
        db.commit()
        db.refresh(user)
        return user

    user = get_user_by_email(db, profile.email)
    if user is None:
        user = create_user(
            db,
            email=profile.email,
            name=profile.name,
            avatar_url=profile.avatar_url,
        )
        create_default_user_settings(db, user.id)
    else:
        update_user_profile(db, user, name=profile.name, avatar_url=profile.avatar_url)

    create_oauth_account(
        db,
        user_id=user.id,
        provider=profile.provider,
        provider_account_id=profile.provider_account_id,
    )
    touch_user_last_login(db, user)
    db.commit()
    db.refresh(user)
    return user

