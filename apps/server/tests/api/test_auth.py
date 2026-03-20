"""Tests for authentication endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.auth.jwt import create_access_token
from codebot.db.models.user import User, UserRole
from codebot.services.auth_service import AuthService


@pytest.mark.integration
class TestRegister:
    """Tests for POST /api/v1/auth (register)."""

    async def test_register_success(self, async_client: AsyncClient) -> None:
        """Registering with valid data returns 201 and user data."""
        response = await async_client.post(
            "/api/v1/auth",
            json={
                "email": "newuser@example.com",
                "password": "strongpass123",
                "name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["email"] == "newuser@example.com"
        assert data["data"]["name"] == "New User"
        assert data["data"]["role"] == "user"
        assert "id" in data["data"]

    async def test_register_duplicate_email(self, async_client: AsyncClient) -> None:
        """Registering with a duplicate email returns 409."""
        payload = {
            "email": "duplicate@example.com",
            "password": "strongpass123",
            "name": "First User",
        }
        response1 = await async_client.post("/api/v1/auth", json=payload)
        assert response1.status_code == 201

        response2 = await async_client.post("/api/v1/auth", json=payload)
        assert response2.status_code == 409


@pytest.mark.integration
class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, async_client: AsyncClient) -> None:
        """Login with valid credentials returns tokens and user data."""
        # Register first
        await async_client.post(
            "/api/v1/auth",
            json={
                "email": "loginuser@example.com",
                "password": "strongpass123",
                "name": "Login User",
            },
        )
        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "loginuser@example.com",
                "password": "strongpass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"
        assert data["data"]["user"]["email"] == "loginuser@example.com"

    async def test_login_invalid_credentials(self, async_client: AsyncClient) -> None:
        """Login with wrong password returns 401."""
        # Register first
        await async_client.post(
            "/api/v1/auth",
            json={
                "email": "badlogin@example.com",
                "password": "correctpass123",
                "name": "Bad Login",
            },
        )
        # Try wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "badlogin@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401


@pytest.mark.integration
class TestMe:
    """Tests for GET /api/v1/auth/me."""

    async def test_me_authenticated(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """GET /me with valid token returns current user."""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "testuser@example.com"

    async def test_me_unauthenticated(self, async_client: AsyncClient) -> None:
        """GET /me without token returns 401."""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401


@pytest.mark.integration
class TestApiKeys:
    """Tests for API key endpoints."""

    async def test_api_key_create(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating an API key returns 201 with raw key."""
        response = await async_client.post(
            "/api/v1/auth/api-keys",
            json={"name": "My CI Key"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "raw_key" in data["data"]
        assert data["data"]["name"] == "My CI Key"


@pytest.mark.integration
class TestRBAC:
    """Tests for role-based access control."""

    async def test_rbac_viewer_cannot_create_project(
        self,
        async_client: AsyncClient,
        test_db_session: AsyncSession,
    ) -> None:
        """A viewer-role user cannot create projects (403)."""
        # Create a viewer user directly
        from codebot.auth.password import hash_password

        viewer = User(
            email="viewer@example.com",
            password_hash=hash_password("viewerpass123"),
            name="Viewer User",
            role=UserRole.VIEWER,
        )
        test_db_session.add(viewer)
        await test_db_session.commit()
        await test_db_session.refresh(viewer)

        # Get token for viewer
        token = create_access_token(viewer.id, viewer.role.value.lower())
        headers = {"Authorization": f"Bearer {token}"}

        # Try to create project
        response = await async_client.post(
            "/api/v1/projects",
            json={"name": "Should Fail"},
            headers=headers,
        )
        assert response.status_code == 403
