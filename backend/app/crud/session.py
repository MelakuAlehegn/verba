from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_session_token
from app.models.auth_session import UserSession


def get_session_by_token(db: Session, token: str) -> UserSession | None:
    token_hash = hash_session_token(token)
    return db.scalar(select(UserSession).where(UserSession.session_hash == token_hash))


def get_active_session_by_token(db: Session, token: str) -> UserSession | None:
    user_session = get_session_by_token(db, token)
    if user_session is None:
        return None
    if user_session.revoked_at is not None:
        return None
    if user_session.expires_at <= datetime.now(timezone.utc):
        return None
    return user_session


def revoke_session(db: Session, user_session: UserSession) -> UserSession:
    user_session.revoked_at = datetime.now(timezone.utc)
    db.flush()
    return user_session

