from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services.session_service import (
    get_authenticated_user_from_session_token,
    logout_session_by_token,
)


def test_get_authenticated_user_from_session_token_returns_user(monkeypatch) -> None:
    db = Mock()
    user = SimpleNamespace(id=uuid4(), email="dev@example.com")
    active_session = SimpleNamespace(user=user)

    monkeypatch.setattr(
        "app.services.session_service.get_active_session_by_token",
        lambda *args, **kwargs: active_session,
    )

    result = get_authenticated_user_from_session_token(db, "session-token")

    assert result is user


def test_logout_session_by_token_noops_when_missing_token() -> None:
    db = Mock()

    logout_session_by_token(db, None)

    db.commit.assert_not_called()

