from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_account import OAuthAccount


def get_oauth_account(
    db: Session,
    *,
    provider: str,
    provider_account_id: str,
) -> OAuthAccount | None:
    statement = select(OAuthAccount).where(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_account_id == provider_account_id,
    )
    return db.scalar(statement)


def create_oauth_account(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    provider_account_id: str,
) -> OAuthAccount:
    oauth_account = OAuthAccount(
        user_id=user_id,
        provider=provider,
        provider_account_id=provider_account_id,
    )
    db.add(oauth_account)
    db.flush()
    return oauth_account
