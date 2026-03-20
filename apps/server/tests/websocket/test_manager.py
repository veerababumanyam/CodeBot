"""Tests for WebSocket manager JWT authentication flow."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import jwt
import pytest

from codebot.auth.jwt import create_access_token, decode_token
from codebot.config import settings


class TestWebSocketAuth:
    """Tests for WebSocket JWT authentication logic."""

    def test_connect_valid_token_decodes(self) -> None:
        """A valid access token decodes successfully with expected fields."""
        user_id = uuid4()
        token = create_access_token(user_id, "user")
        payload = decode_token(token)

        assert payload["type"] == "access"
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "user"

    def test_connect_without_token_raises(self) -> None:
        """An empty or invalid token raises InvalidTokenError."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("")

    def test_connect_with_expired_token_raises(self) -> None:
        """An expired token raises ExpiredSignatureError."""
        expired_token = jwt.encode(
            {
                "exp": datetime(2020, 1, 1),
                "sub": "test-user",
                "type": "access",
            },
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(expired_token)

    def test_connect_with_wrong_secret_raises(self) -> None:
        """A token signed with the wrong secret is rejected."""
        token = jwt.encode(
            {
                "exp": datetime(2030, 1, 1),
                "sub": "test-user",
                "type": "access",
            },
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(jwt.InvalidSignatureError):
            decode_token(token)

    def test_manager_imports(self) -> None:
        """Socket.IO server and ASGI app are importable and configured."""
        from codebot.websocket.manager import sio, socket_app

        assert sio is not None
        assert socket_app is not None
