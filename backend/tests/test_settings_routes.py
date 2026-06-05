from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import create_app


def test_settings_routes_are_registered(monkeypatch) -> None:
    app = create_app()
    current_user = SimpleNamespace(id=uuid4())
    settings_payload = SimpleNamespace(
        default_provider="groq",
        theme="system",
        retrieval_settings={},
        preferences={},
    )

    app.dependency_overrides[get_current_user] = lambda: current_user
    monkeypatch.setattr(
        "app.api.v1.endpoints.settings.get_or_create_user_settings_for_user",
        lambda *args, **kwargs: settings_payload,
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.settings.update_user_settings_for_user",
        lambda *args, **kwargs: SimpleNamespace(
            default_provider="groq",
            theme=args[2].theme,
            retrieval_settings={},
            preferences={},
        ),
    )

    client = TestClient(app)

    read_response = client.get("/api/v1/settings")
    patch_response = client.patch("/api/v1/settings", json={"theme": "dark"})

    assert read_response.status_code == 200
    assert read_response.json()["theme"] == "system"
    assert patch_response.status_code == 200
    assert patch_response.json()["theme"] == "dark"
