from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token

from app.core.config import Settings
from app.schemas.auth import OAuthProfile


def build_google_authorization_url(settings: Settings, state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": settings.google_scope,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{settings.google_auth_url}?{urlencode(params)}"


def exchange_google_code_for_tokens(settings: Settings, code: str) -> dict[str, str]:
    payload = urlencode(
        {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    request = Request(
        settings.google_token_url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urlopen(request, timeout=10) as response:
        token_payload = json.loads(response.read().decode("utf-8"))

    if "id_token" not in token_payload:
        raise ValueError("Google token response did not include an id_token")

    return token_payload


def verify_google_id_token(settings: Settings, raw_id_token: str) -> OAuthProfile:
    payload = id_token.verify_oauth2_token(raw_id_token, GoogleRequest(), settings.google_client_id)

    email = payload.get("email")
    provider_account_id = payload.get("sub")
    if not email or not provider_account_id:
        raise ValueError("Google ID token is missing required claims")

    return OAuthProfile(
        provider="google",
        provider_account_id=provider_account_id,
        email=email,
        name=payload.get("name"),
        avatar_url=payload.get("picture"),
    )


def exchange_code_for_oauth_profile(settings: Settings, code: str) -> OAuthProfile:
    token_payload = exchange_google_code_for_tokens(settings, code)
    return verify_google_id_token(settings, token_payload["id_token"])
