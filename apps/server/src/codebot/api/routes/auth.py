"""Authentication endpoints for the CodeBot API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.deps import get_current_user, get_db
from codebot.api.envelope import ResponseEnvelope
from codebot.api.schemas.auth import (
    ApiKeyCreatedResponse,
    ApiKeyCreateRequest,
    ApiKeyResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RefreshTokenResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from codebot.auth.jwt import create_access_token, create_refresh_token, decode_token
from codebot.config import settings
from codebot.db.models.user import User
from codebot.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(db)


@router.post(
    "",
    response_model=ResponseEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(_get_auth_service)],
) -> ResponseEnvelope[UserResponse]:
    """Register a new user account.

    Args:
        body: Registration data (email, password, name).
        service: Auth service dependency.

    Returns:
        Created user profile wrapped in response envelope.
    """
    user = await service.register(
        email=body.email,
        password=body.password,
        name=body.name,
        organization=body.organization,
    )
    return ResponseEnvelope(data=UserResponse.model_validate(user))


@router.post(
    "/login",
    response_model=ResponseEnvelope[TokenResponse],
)
async def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(_get_auth_service)],
) -> ResponseEnvelope[TokenResponse]:
    """Authenticate and receive JWT tokens.

    Args:
        body: Login credentials (email, password).
        service: Auth service dependency.

    Returns:
        Access and refresh tokens with user profile.
    """
    user = await service.login(email=body.email, password=body.password)
    access_token = create_access_token(user.id, user.role.value.lower())
    refresh_token = create_refresh_token(user.id)
    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )
    return ResponseEnvelope(data=token_data)


@router.post(
    "/refresh",
    response_model=ResponseEnvelope[RefreshTokenResponse],
)
async def refresh(
    body: RefreshRequest,
) -> ResponseEnvelope[RefreshTokenResponse]:
    """Refresh an access token using a valid refresh token.

    Args:
        body: Refresh token.

    Returns:
        New access token.
    """
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from None
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    user_id = UUID(payload["sub"])
    role = payload.get("role", "user")
    new_access_token = create_access_token(user_id, role)
    return ResponseEnvelope(
        data=RefreshTokenResponse(
            access_token=new_access_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Logout (client-side token discard for v1).

    Token revocation via Redis is deferred to a future plan.

    Args:
        body: Logout request with refresh token.
        current_user: The authenticated user.

    Returns:
        204 No Content.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=ResponseEnvelope[UserResponse],
)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> ResponseEnvelope[UserResponse]:
    """Get the current authenticated user's profile.

    Args:
        current_user: The authenticated user.

    Returns:
        User profile wrapped in response envelope.
    """
    return ResponseEnvelope(data=UserResponse.model_validate(current_user))


@router.post(
    "/api-keys",
    response_model=ResponseEnvelope[ApiKeyCreatedResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(_get_auth_service)],
) -> ResponseEnvelope[ApiKeyCreatedResponse]:
    """Create a new API key for the authenticated user.

    The raw key is only returned once at creation time.

    Args:
        body: API key creation data (name).
        current_user: The authenticated user.
        service: Auth service dependency.

    Returns:
        Created API key with raw key value.
    """
    api_key_obj, raw_key = await service.create_api_key(user_id=current_user.id, name=body.name)
    response_data = ApiKeyCreatedResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        key_prefix=api_key_obj.key_prefix,
        created_at=api_key_obj.created_at,
        last_used_at=api_key_obj.last_used_at,
        raw_key=raw_key,
    )
    return ResponseEnvelope(data=response_data)


@router.get(
    "/api-keys",
    response_model=ResponseEnvelope[list[ApiKeyResponse]],
)
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(_get_auth_service)],
) -> ResponseEnvelope[list[ApiKeyResponse]]:
    """List all API keys for the authenticated user.

    Args:
        current_user: The authenticated user.
        service: Auth service dependency.

    Returns:
        List of API keys (without raw key values).
    """
    keys = await service.list_api_keys(user_id=current_user.id)
    return ResponseEnvelope(data=[ApiKeyResponse.model_validate(k) for k in keys])
