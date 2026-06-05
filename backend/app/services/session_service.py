from __future__ import annotations

from sqlalchemy.orm import Session

from app.crud.session import get_active_session_by_token, get_session_by_token, revoke_session
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

