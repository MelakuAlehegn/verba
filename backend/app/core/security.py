from __future__ import annotations

import hashlib

SESSION_COOKIE_NAME = "session_token"


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

