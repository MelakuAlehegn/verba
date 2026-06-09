from pydantic import BaseModel, EmailStr, Field


class OAuthProfile(BaseModel):
    provider: str
    provider_account_id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

