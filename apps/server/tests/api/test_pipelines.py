"""Tests for pipeline CRUD and lifecycle endpoints."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


async def _create_project(
    client: AsyncClient, headers: dict[str, str], name: str = "Test Project"
) -> str:
    """Helper to create a project and return its ID."""
    response = await client.post(
        "/api/v1/projects",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


async def _create_pipeline(
    client: AsyncClient,
    headers: dict[str, str],
    project_id: str,
    mode: str = "full",
) -> str:
    """Helper to create a pipeline and return its ID."""
    response = await client.post(
        f"/api/v1/projects/{project_id}/pipelines",
        json={"mode": mode},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


@pytest.mark.integration
class TestCreatePipeline:
    """Tests for POST /api/v1/projects/{id}/pipelines."""

    async def test_create_pipeline(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating a pipeline with mode=full returns 201 with pending status."""
        project_id = await _create_project(async_client, auth_headers)
        response = await async_client.post(
            f"/api/v1/projects/{project_id}/pipelines",
            json={"mode": "full"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "pending"

    async def test_create_pipeline_quick_preset(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating a pipeline with mode=quick produces planning, implementation, testing phases."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id, "quick")

        phases_resp = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}/phases",
            headers=auth_headers,
        )
        assert phases_resp.status_code == 200
        phase_names = [p["name"] for p in phases_resp.json()["data"]]
        assert phase_names == ["planning", "implementation", "testing"]

    async def test_create_pipeline_review_only_preset(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Creating a pipeline with mode=review_only produces review, testing phases."""
        project_id = await _create_project(async_client, auth_headers)

        response = await async_client.post(
            f"/api/v1/projects/{project_id}/pipelines",
            json={"mode": "review_only"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        pipeline_id = response.json()["data"]["id"]

        phases_resp = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}/phases",
            headers=auth_headers,
        )
        assert phases_resp.status_code == 200
        phase_names = [p["name"] for p in phases_resp.json()["data"]]
        assert phase_names == ["review", "testing"]


@pytest.mark.integration
class TestPipelineLifecycle:
    """Tests for pipeline lifecycle transitions."""

    async def test_start_pipeline(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Starting a pending pipeline transitions it to running."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/start",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "running"

    async def test_pause_pipeline(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Pausing a running pipeline transitions it to paused."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/start", headers=auth_headers
        )
        response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/pause", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "paused"

    async def test_resume_pipeline(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Resuming a paused pipeline transitions it back to running."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/start", headers=auth_headers
        )
        await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/pause", headers=auth_headers
        )
        response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/resume", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "running"

    async def test_cancel_pipeline(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Cancelling a running pipeline transitions it to cancelled."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/start", headers=auth_headers
        )
        response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/cancel", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "cancelled"

    async def test_invalid_transition_start_running(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Starting an already-running pipeline returns 400."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/start", headers=auth_headers
        )
        response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/start", headers=auth_headers
        )
        assert response.status_code == 400

    async def test_start_pipeline_publishes_pipeline_update(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Starting a pipeline emits a pipeline:update event for live dashboards."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        bus_mock = AsyncMock()

        with patch(
            "codebot.api.routes.pipelines.get_event_bus",
            AsyncMock(return_value=bus_mock),
        ):
            response = await async_client.post(
                f"/api/v1/pipelines/{pipeline_id}/start",
                headers=auth_headers,
            )

        assert response.status_code == 200
        bus_mock.publish.assert_awaited_once()
        event_name, payload = bus_mock.publish.await_args.args
        assert event_name == "pipeline:update"

        decoded = json.loads(payload.decode("utf-8"))
        assert decoded["pipeline_id"] == pipeline_id
        assert decoded["project_id"] == project_id
        assert decoded["status"] == "running"
        assert decoded["error_message"] is None
        assert decoded["started_at"] is not None


@pytest.mark.integration
class TestListPipelines:
    """Tests for GET /api/v1/projects/{id}/pipelines."""

    async def test_list_pipelines(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Listing pipelines returns created pipelines."""
        project_id = await _create_project(async_client, auth_headers)
        await _create_pipeline(async_client, auth_headers, project_id)
        await _create_pipeline(async_client, auth_headers, project_id)

        response = await async_client.get(
            f"/api/v1/projects/{project_id}/pipelines",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2


@pytest.mark.integration
class TestGetPipeline:
    """Tests for GET /api/v1/pipelines/{id} and phases."""

    async def test_get_pipeline_detail(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Getting a pipeline by ID returns detail including graph_definition."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        response = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "graph_definition" in data

    async def test_get_pipeline_phases(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Getting phases of a full pipeline returns 10 phases."""
        project_id = await _create_project(async_client, auth_headers)
        pipeline_id = await _create_pipeline(async_client, auth_headers, project_id)

        response = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}/phases",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 10
