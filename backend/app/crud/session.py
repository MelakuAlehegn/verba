from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_session_token
from app.models.auth_session import UserSession


def get_session_by_token(db: Session, token: str) -> UserSession | None:
    token_hash = hash_session_token(token)
    return db.scalar(select(UserSession).where(UserSession.session_hash == token_hash))


def create_session(
    db: Session,
    *,
    user_id: UUID,
    session_token: str,
    expires_at: datetime,
    user_agent: str | None = None,
    ip: str | None = None,
) -> UserSession:
    user_session = UserSession(
        user_id=user_id,
        session_hash=hash_session_token(session_token),
        expires_at=expires_at,
        user_agent=user_agent,
        ip=ip,
    )
    db.add(user_session)
    db.flush()
    return user_session


def get_active_session_by_token(db: Session, token: str) -> UserSession | None:
    user_session = get_session_by_token(db, token)
    if user_session is None:
        return None
    if user_session.revoked_at is not None:
        return None
    if user_session.expires_at <= datetime.now(UTC):
        return None
    return user_session


def revoke_session(db: Session, user_session: UserSession) -> UserSession:
    user_session.revoked_at = datetime.now(UTC)
    db.flush()
    return user_session
