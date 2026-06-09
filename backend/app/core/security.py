from __future__ import annotations

import hashlib
import secrets

import bcrypt

SESSION_COOKIE_NAME = "session_token"
OAUTH_STATE_COOKIE_NAME = "oauth_state"


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    # Opaque session tokens are high-entropy and looked up by exact match,
    # so a fast hash (sha256) is the right tool here.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    # Passwords are low-entropy and attacker-guessable, so they need a slow,
    # salted hash (bcrypt) — deliberately the opposite of session tokens.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
