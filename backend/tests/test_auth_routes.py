from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import OAUTH_STATE_COOKIE_NAME
from app.main import create_app

AUTH_MODULE = "app.api.v1.endpoints.auth"


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


def _user(**overrides) -> SimpleNamespace:
    base = dict(
        id=uuid4(),
        email="dev@example.com",
        name="Dev",
        avatar_url=None,
        onboarded_at=None,
        last_login_at=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_register_creates_account_and_sets_session_cookie(monkeypatch) -> None:
    app = create_app()
    monkeypatch.setattr(f"{AUTH_MODULE}.register_user_with_password", lambda *a, **k: _user())
    monkeypatch.setattr(f"{AUTH_MODULE}.create_session_for_user", lambda *a, **k: "session-token")

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dev@example.com", "password": "supersecret", "name": "Dev"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "dev@example.com"
    assert "session_token=session-token" in response.headers["set-cookie"]


def test_register_duplicate_email_returns_409(monkeypatch) -> None:
    app = create_app()
    monkeypatch.setattr(f"{AUTH_MODULE}.register_user_with_password", lambda *a, **k: None)

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "taken@example.com", "password": "supersecret"},
    )

    assert response.status_code == 409


def test_register_short_password_returns_422() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dev@example.com", "password": "short"},
    )

    assert response.status_code == 422


def test_login_valid_credentials_sets_session_cookie(monkeypatch) -> None:
    app = create_app()
    monkeypatch.setattr(f"{AUTH_MODULE}.authenticate_user", lambda *a, **k: _user())
    monkeypatch.setattr(f"{AUTH_MODULE}.create_session_for_user", lambda *a, **k: "session-token")

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dev@example.com", "password": "supersecret"},
    )

    assert response.status_code == 200
    assert "session_token=session-token" in response.headers["set-cookie"]


def test_login_invalid_credentials_returns_401(monkeypatch) -> None:
    app = create_app()
    monkeypatch.setattr(f"{AUTH_MODULE}.authenticate_user", lambda *a, **k: None)

    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dev@example.com", "password": "wrong"},
    )

    assert response.status_code == 401


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

    monkeypatch.setattr(
        f"{AUTH_MODULE}.exchange_code_for_oauth_profile", lambda *a, **k: SimpleNamespace()
    )
    monkeypatch.setattr(
        f"{AUTH_MODULE}.upsert_user_from_oauth_profile", lambda *a, **k: current_user
    )
    monkeypatch.setattr(
        f"{AUTH_MODULE}.create_session_for_user", lambda *a, **k: "session-token"
    )

    client = TestClient(app)
    client.cookies.set(OAUTH_STATE_COOKIE_NAME, "state-token")

    response = client.get(
        "/api/v1/auth/google/callback?code=code-token&state=state-token",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].endswith("/auth/callback")
    assert "session_token=session-token" in response.headers["set-cookie"]
