from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
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


def register_user_with_password(
    db: Session,
    *,
    email: str,
    password: str,
    name: str | None = None,
) -> User | None:
    """Create a password-backed account. Returns None if the email is taken."""
    if get_user_by_email(db, email) is not None:
        return None

    user = create_user(db, email=email, name=name, password_hash=hash_password(password))
    create_default_user_settings(db, user.id)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    """Return the user for valid credentials, else None.

    A single None return for "no such user", "OAuth-only user", and "wrong
    password" avoids leaking which emails are registered.
    """
    user = get_user_by_email(db, email)
    if user is None or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None

    touch_user_last_login(db, user)
    db.commit()
    db.refresh(user)
    return user

