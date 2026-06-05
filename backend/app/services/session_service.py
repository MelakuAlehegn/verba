from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import generate_token
from app.crud.session import create_session, get_active_session_by_token, get_session_by_token, revoke_session
from app.models.user import User


def get_authenticated_user_from_session_token(db: Session, session_token: str) -> User | None:
    active_session = get_active_session_by_token(db, session_token)
    if active_session is None:
        return None
    return active_session.user


def logout_session_by_token(db: Session, session_token: str | None) -> None:
    if session_token is None:
        return

    user_session = get_session_by_token(db, session_token)
    if user_session is None or user_session.revoked_at is not None:
        return

    revoke_session(db, user_session)
    db.commit()


def create_session_for_user(
    db: Session,
    user: User,
    settings: Settings,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> str:
    session_token = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.session_ttl_days)
    create_session(
        db,
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at,
        user_agent=user_agent,
        ip=ip_address,
    )
    db.commit()
    return session_token
