from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SESSION_COOKIE_NAME
from app.models.user import User
from app.services.session_service import get_authenticated_user_from_session_token


def get_optional_session_token(
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str | None:
    return session_token


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Depends(get_optional_session_token),
) -> User:
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_authenticated_user_from_session_token(db, session_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return user

