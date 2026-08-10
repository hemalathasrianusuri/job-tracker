import uuid

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    target_role: str | None
    experience_years: float | None


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Note: refresh_token is intentionally NOT included here — it's set as an
    # httpOnly cookie by the router, never exposed to JS on the frontend.


class RefreshRequest(BaseModel):
    """Only used for non-browser clients (e.g. mobile) that can't rely on cookies."""
    refresh_token: str
