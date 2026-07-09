from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import create_app


def _client_with_routes() -> TestClient:
    app = create_app()

    @app.get("/api/v1/_boom")
    def boom() -> None:
        raise RuntimeError("kaboom")

    @app.get("/api/v1/_teapot")
    def teapot() -> None:
        raise HTTPException(status_code=418, detail="I'm a teapot")

    @app.get("/api/v1/_needsint")
    def needsint(n: int) -> dict[str, int]:
        return {"n": n}

    # Don't let TestClient re-raise server errors — we want the 500 response.
    return TestClient(app, raise_server_exceptions=False)


def test_http_exception_uses_envelope() -> None:
    response = _client_with_routes().get("/api/v1/_teapot")

    assert response.status_code == 418
    body = response.json()
    assert body["error"]["code"] == "im_a_teapot"
    assert body["error"]["message"] == "I'm a teapot"
    assert body["request_id"]  # correlation id included


def test_unhandled_exception_is_generic_500_with_request_id() -> None:
    response = _client_with_routes().get("/api/v1/_boom", headers={"X-Request-ID": "trace-err"})

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "Something went wrong."  # internals not leaked
    assert "kaboom" not in response.text
    assert body["request_id"] == "trace-err"


def test_validation_error_uses_envelope() -> None:
    response = _client_with_routes().get("/api/v1/_needsint?n=abc")

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "n" in body["error"]["message"]  # names the offending field
    assert body["request_id"]
