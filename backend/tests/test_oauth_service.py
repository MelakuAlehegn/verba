from app.core.config import Settings
from app.services.oauth_service import build_google_authorization_url


def test_build_google_authorization_url_includes_expected_query_params() -> None:
    settings = Settings(
        google_client_id="client-id",
        google_redirect_uri="http://127.0.0.1:8000/api/v1/auth/google/callback",
    )

    url = build_google_authorization_url(settings, "state-token")

    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=client-id" in url
    assert "state=state-token" in url
    assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fv1%2Fauth%2Fgoogle%2Fcallback" in url

