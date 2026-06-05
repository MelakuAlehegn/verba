from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_session_token
from app.models.user import User
from app.schemas.user import UserRead
from app.services.session_service import logout_session_by_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Depends(get_optional_session_token),
) -> Response:
    logout_session_by_token(db, session_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
