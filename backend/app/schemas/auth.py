from pydantic import BaseModel


class OAuthProfile(BaseModel):
    provider: str
    provider_account_id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None

