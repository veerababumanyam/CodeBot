"""FastAPI dependency injection providers for auth and database sessions."""

from collections.abc import AsyncGenerator, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.auth.api_key import hash_api_key
from codebot.auth.jwt import decode_token
from codebot.db.engine import async_session_factory
from codebot.db.models.user import ApiKey, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    The session is automatically closed when the request finishes.
    """
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,  # type: ignore[assignment]
) -> User:
    """Resolve the current user from a JWT token or API key.

    Args:
        token: Bearer token from the Authorization header.
        api_key: API key from the X-API-Key header.
        db: Database session.

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException: 401 if neither credential is provided or is invalid.
    """
    if token is not None:
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await db.get(User, UUID(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    if api_key is not None:
        key_hash = hash_api_key(api_key)
        result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
        api_key_obj = result.scalar_one_or_none()
        if api_key_obj is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        user = await db.get(User, api_key_obj.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key owner not found",
            )
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles: str) -> Callable:
    """Create a dependency that enforces role-based access control.

    Args:
        *roles: Allowed role names (case-insensitive).

    Returns:
        A FastAPI dependency function that raises 403 if the user's role
        is not in the allowed set.
    """
    allowed = [r.lower() for r in roles]

    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role.value.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check_role
