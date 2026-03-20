"""Tests for project CRUD endpoints."""

from __future__ import annotations

import base64

import pytest
from httpx import AsyncClient

from codebot.config import settings


def _make_pdf_bytes(text: str) -> bytes:
    """Build a tiny single-page PDF containing extractable text."""
    content_stream = f"BT\n/F1 18 Tf\n72 72 Td\n({text}) Tj\nET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content_stream.encode('utf-8'))} >>\nstream\n{content_stream}\nendstream",
    ]

    parts: list[bytes] = [b"%PDF-1.4\n"]
    offsets: list[int] = []

    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in parts))
        parts.append(f"{index} 0 obj\n{obj}\nendobj\n".encode("utf-8"))

    xref_offset = sum(len(part) for part in parts)
    xref_entries = [b"0000000000 65535 f \n"]
    xref_entries.extend(f"{offset:010d} 00000 n \n".encode("utf-8") for offset in offsets)
    parts.extend(
        [
            f"xref\n0 {len(objects) + 1}\n".encode("utf-8"),
            *xref_entries,
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode("utf-8"),
        ]
    )

    return b"".join(parts)


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

    async def test_create_project_from_uploaded_text_file(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Uploading a text PRD file extracts text into project detail."""
        encoded = base64.b64encode(b"# PRD\nBuild a collaborative whiteboard").decode("utf-8")
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "Uploaded PRD Project",
                "description": "Created from file",
                "prd_source": "file",
                "prd_file": encoded,
                "source_name": "requirements.md",
                "source_media_type": "text/markdown",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        project_id = response.json()["data"]["id"]

        detail_response = await async_client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        assert "Build a collaborative whiteboard" in detail_response.json()["data"]["prd_content"]

    async def test_create_project_from_uploaded_pdf_file(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Uploading a PDF PRD file extracts text into project detail."""
        encoded = base64.b64encode(_make_pdf_bytes("Build a support portal")).decode("utf-8")
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "Uploaded PDF Project",
                "description": "Created from pdf",
                "prd_source": "file",
                "prd_file": encoded,
                "source_name": "requirements.pdf",
                "source_media_type": "application/pdf",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        project_id = response.json()["data"]["id"]

        detail_response = await async_client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        assert "Build a support portal" in detail_response.json()["data"]["prd_content"]

    async def test_create_project_missing_source_payload_fails(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Selecting a non-text source without its payload returns 422."""
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "Broken Source Project",
                "prd_source": "url",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_brownfield_project_persists_repository_fields(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Import-style creation stores repository metadata and project type."""
        response = await async_client.post(
            "/api/v1/projects",
            json={
                "name": "Imported Project",
                "prd_source": "text",
                "prd_content": "Improve the existing admin dashboard",
                "project_type": "brownfield",
                "repository_url": "https://github.com/example/repo.git",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        project_id = response.json()["data"]["id"]
        assert response.json()["data"]["project_type"] == "brownfield"

        detail_response = await async_client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["repository_url"] == "https://github.com/example/repo.git"

    async def test_unauthorized_access(self, async_client: AsyncClient) -> None:
        """Accessing projects without auth returns 401."""
        response = await async_client.get("/api/v1/projects")
        expected_status = 200 if settings.debug else 401
        assert response.status_code == expected_status


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
