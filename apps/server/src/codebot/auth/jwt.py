"""JWT token creation and verification for CodeBot authentication."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from codebot.config import settings


def create_access_token(user_id: UUID, role: str) -> str:
    """Create a short-lived JWT access token.

    Args:
        user_id: The user's UUID.
        role: The user's role string (e.g. "admin", "user", "viewer").

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "iat": now,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID) -> str:
    """Create a long-lived JWT refresh token.

    Args:
        user_id: The user's UUID.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
        "iat": now,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Args:
        token: The encoded JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    return jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
