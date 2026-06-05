from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.core.security import OAUTH_STATE_COOKIE_NAME
from app.core.database import get_db
from app.main import create_app


def test_auth_me_returns_current_user_payload() -> None:
    app = create_app()
    current_user = SimpleNamespace(
        id=uuid4(),
        email="dev@example.com",
        name="Dev",
        avatar_url=None,
        onboarded_at=None,
        last_login_at=None,
    )

    app.dependency_overrides[get_current_user] = lambda: current_user

    client = TestClient(app)
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == "dev@example.com"


def test_start_google_oauth_redirects_and_sets_state_cookie(monkeypatch) -> None:
    app = create_app()
    monkeypatch.setattr("app.api.v1.endpoints.auth.generate_token", lambda: "state-token")

    client = TestClient(app)
    response = client.get("/api/v1/auth/google", follow_redirects=False)

    assert response.status_code == 303
    assert "accounts.google.com" in response.headers["location"]
    assert f"{OAUTH_STATE_COOKIE_NAME}=state-token" in response.headers["set-cookie"]


def test_google_callback_sets_session_cookie_and_redirects(monkeypatch) -> None:
    app = create_app()
    db = SimpleNamespace()
    current_user = SimpleNamespace(id=uuid4(), email="dev@example.com")

    app.dependency_overrides[get_db] = lambda: db

    monkeypatch.setattr("app.api.v1.endpoints.auth.exchange_code_for_oauth_profile", lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr("app.api.v1.endpoints.auth.upsert_user_from_oauth_profile", lambda *args, **kwargs: current_user)
    monkeypatch.setattr("app.api.v1.endpoints.auth.create_session_for_user", lambda *args, **kwargs: "session-token")

    client = TestClient(app)
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, "state-token")

    response = client.get(
        "/api/v1/auth/google/callback?code=code-token&state=state-token",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/app")
    assert "session_token=session-token" in response.headers["set-cookie"]
