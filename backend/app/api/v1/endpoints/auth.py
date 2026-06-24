from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_session_token
from app.core.security import OAUTH_STATE_COOKIE_NAME, SESSION_COOKIE_NAME, generate_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserRead, UserUpdate
from app.services.auth_service import (
    authenticate_user,
    register_user_with_password,
    update_current_user,
    upsert_user_from_oauth_profile,
)
from app.services.oauth_service import (
    build_google_authorization_url,
    exchange_code_for_oauth_profile,
)
from app.services.session_service import create_session_for_user, logout_session_by_token

router = APIRouter(prefix="/auth", tags=["auth"])


def set_session_cookie(response: Response, session_token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.session_ttl_days * 24 * 60 * 60,
    )


def _issue_session(
    response: Response, db: Session, user: User, request: Request, settings: Settings
) -> None:
    session_token = create_session_for_user(
        db,
        user,
        settings,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client is not None else None,
    )
    set_session_cookie(response, session_token, settings)


@router.get("/google")
def start_google_oauth() -> RedirectResponse:
    settings = get_settings()
    oauth_state = generate_token()
    redirect_response = RedirectResponse(
        url=build_google_authorization_url(settings, oauth_state),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    redirect_response.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=oauth_state,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=600,
    )
    return redirect_response


@router.get("/google/callback")
def handle_google_oauth_callback(
    request: Request,
    db: Session = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
) -> RedirectResponse:
    settings = get_settings()
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")
    if code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code"
        )

    profile = exchange_code_for_oauth_profile(settings, code)
    user = upsert_user_from_oauth_profile(db, profile)
    session_token = create_session_for_user(
        db,
        user,
        settings,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client is not None else None,
    )

    # Hand off to the frontend's post-auth handler, which hydrates the user
    # and routes to onboarding (new user) or the workspace. Redirecting
    # straight to /app would skip that onboarding decision.
    redirect_response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    set_session_cookie(redirect_response, session_token, settings)
    redirect_response.delete_cookie(OAUTH_STATE_COOKIE_NAME, path="/")
    return redirect_response


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_with_password(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> UserRead:
    settings = get_settings()
    user = register_user_with_password(
        db,
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    _issue_session(response, db, user, request, settings)
    return UserRead.model_validate(user)


@router.post("/login", response_model=UserRead)
def login_with_password(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> UserRead:
    settings = get_settings()
    user = authenticate_user(db, email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    _issue_session(response, db, user, request, settings)
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
def update_current_user_endpoint(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    user = update_current_user(
        db,
        current_user,
        name=payload.name,
        avatar_url=payload.avatar_url,
        onboarded=payload.onboarded,
    )
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_current_user(
    response: Response,
    db: Session = Depends(get_db),
    session_token: str | None = Depends(get_optional_session_token),
) -> None:
    logout_session_by_token(db, session_token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
