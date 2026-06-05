from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
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
