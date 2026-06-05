from __future__ import annotations

import hashlib
import secrets

SESSION_COOKIE_NAME = "session_token"
OAUTH_STATE_COOKIE_NAME = "oauth_state"


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
