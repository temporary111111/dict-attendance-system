"""Schemas para sa admin authentication endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request body ng admin login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Token details na ibabalik after successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
