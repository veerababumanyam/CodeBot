"""Pydantic v2 schemas for authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=255)
    organization: str | None = None


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request body for logout (client-side token discard for v1)."""

    refresh_token: str


class UserResponse(BaseModel):
    """User profile data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    role: str
    organization: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def role_to_string(cls, v: object) -> str:
        """Convert UserRole enum to lowercase string."""
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()


class TokenResponse(BaseModel):
    """Response containing JWT access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    """Response containing a new access token after refresh."""

    access_token: str
    expires_in: int


class ApiKeyCreateRequest(BaseModel):
    """Request body for creating an API key."""

    name: str = Field(min_length=1, max_length=255)


class ApiKeyResponse(BaseModel):
    """API key data returned in list responses (no raw key)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None


class ApiKeyCreatedResponse(ApiKeyResponse):
    """API key data returned once at creation (includes raw key)."""

    raw_key: str
