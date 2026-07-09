from fastapi.testclient import TestClient

from app.main import create_app
from app.services import readiness_service

SVC = "app.services.readiness_service"
ENDPOINT = "app.api.v1.endpoints.health"


def test_get_readiness_all_ok(monkeypatch) -> None:
    monkeypatch.setattr(f"{SVC}._check_database", lambda: None)
    monkeypatch.setattr(f"{SVC}._check_qdrant", lambda: None)
    monkeypatch.setattr(f"{SVC}._check_redis", lambda: None)

    ready, checks = readiness_service.get_readiness()

    assert ready is True
    assert checks == {"database": "ok", "qdrant": "ok", "redis": "ok"}


def test_get_readiness_reports_failing_dependency(monkeypatch) -> None:
    def boom() -> None:
        raise RuntimeError("qdrant down")

    monkeypatch.setattr(f"{SVC}._check_database", lambda: None)
    monkeypatch.setattr(f"{SVC}._check_qdrant", boom)
    monkeypatch.setattr(f"{SVC}._check_redis", lambda: None)

    ready, checks = readiness_service.get_readiness()

    assert ready is False
    assert checks["qdrant"] == "error"
    assert checks["database"] == "ok"  # isolated: one failure doesn't hide the rest


def test_readyz_returns_200_when_ready(monkeypatch) -> None:
    monkeypatch.setattr(f"{ENDPOINT}.get_readiness", lambda: (True, {"database": "ok"}))
    response = TestClient(create_app()).get("/api/v1/readyz")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readyz_returns_503_when_a_dependency_is_down(monkeypatch) -> None:
    monkeypatch.setattr(
        f"{ENDPOINT}.get_readiness", lambda: (False, {"database": "ok", "redis": "error"})
    )
    response = TestClient(create_app()).get("/api/v1/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["redis"] == "error"
