"""Tests for project CRUD endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestCreateProject:
    """Tests for POST /api/v1/projects."""

    async def test_create_project(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating a project with valid data returns 201."""
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "My Test Project",
                "description": "A test project",
                "prd_content": "Build a todo app",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["name"] == "My Test Project"
        assert data["data"]["status"] == "created"

    async def test_unauthorized_access(self, async_client: AsyncClient) -> None:
        """Accessing projects without auth returns 401."""
        response = await async_client.get("/api/v1/projects")
        assert response.status_code == 401


@pytest.mark.integration
class TestListProjects:
    """Tests for GET /api/v1/projects."""

    async def test_list_projects(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Listing projects returns paginated results."""
        # Create 2 projects
        for i in range(2):
            await async_client.post(
                "/api/v1/projects",
                json={"name": f"Project {i}"},
                headers=auth_headers,
            )

        response = await async_client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2


@pytest.mark.integration
class TestGetProject:
    """Tests for GET /api/v1/projects/{id}."""

    async def test_get_project(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Getting a project by ID returns full detail."""
        # Create
        create_response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "Detail Project",
                "prd_content": "Some PRD content",
            },
            headers=auth_headers,
        )
        project_id = create_response.json()["data"]["id"]

        # Get
        response = await async_client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["prd_content"] == "Some PRD content"


@pytest.mark.integration
class TestUpdateProject:
    """Tests for PATCH /api/v1/projects/{id}."""

    async def test_update_project(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Updating a project changes its fields."""
        # Create
        create_response = await async_client.post(
            "/api/v1/projects",
            json={"name": "Original Name"},
            headers=auth_headers,
        )
        project_id = create_response.json()["data"]["id"]

        # Update
        response = await async_client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Name"


@pytest.mark.integration
class TestDeleteProject:
    """Tests for DELETE /api/v1/projects/{id}."""

    async def test_delete_project(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Deleting a project returns 204, then GET returns 404."""
        # Create
        create_response = await async_client.post(
            "/api/v1/projects",
            json={"name": "To Delete"},
            headers=auth_headers,
        )
        project_id = create_response.json()["data"]["id"]

        # Delete
        response = await async_client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify gone
        get_response = await async_client.get(
            f"/api/v1/projects/{project_id}", headers=auth_headers
        )
        assert get_response.status_code == 404
