"""Tests for project brainstorm session endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.db.models.project import PhaseStatus, PipelinePhase


async def _create_brainstorm_project(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> str:
    response = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "Brainstorm Project",
            "description": "Build a lightweight workflow assistant for operations teams",
            "settings": {"kickoff_flow": "brainstorm", "pipeline_preset": "quick"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "brainstorming"
    return response.json()["data"]["id"]


@pytest.mark.integration
class TestBrainstormSession:
    """Tests for brainstorm lifecycle endpoints."""

    async def test_start_brainstorm_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Starting brainstorm creates a reusable guided session."""
        project_id = await _create_brainstorm_project(async_client, auth_headers)

        response = await async_client.post(
            f"/api/v1/projects/{project_id}/brainstorm/start",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "active"
        assert data["summary"]["recommended_preset"] == "quick"
        assert len(data["questions"]) >= 1
        assert len(data["messages"]) >= 1

    async def test_finalize_requires_blockers_to_be_answered(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Finalize is blocked until required brainstorm answers are provided."""
        project_id = await _create_brainstorm_project(async_client, auth_headers)

        await async_client.post(
            f"/api/v1/projects/{project_id}/brainstorm/start",
            headers=auth_headers,
        )
        finalize_response = await async_client.post(
            f"/api/v1/projects/{project_id}/brainstorm/finalize",
            headers=auth_headers,
        )

        assert finalize_response.status_code == 409

    async def test_brainstorm_answers_can_finalize_project(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Answering required questions finalizes brainstorm into planning."""
        project_id = await _create_brainstorm_project(async_client, auth_headers)

        start_response = await async_client.post(
            f"/api/v1/projects/{project_id}/brainstorm/start",
            headers=auth_headers,
        )
        assert start_response.status_code == 200
        session = start_response.json()["data"]

        for _ in range(10):
            required_questions = [
                question
                for question in session["questions"]
                if question["required"] and question["status"] != "answered"
            ]
            if not required_questions:
                break

            question = required_questions[0]
            respond_response = await async_client.post(
                f"/api/v1/projects/{project_id}/brainstorm/respond",
                json={
                    "question_id": question["id"],
                    "content": f"Answer for {question['category']}.",
                },
                headers=auth_headers,
            )
            assert respond_response.status_code == 200
            session = respond_response.json()["data"]

        finalize_response = await async_client.post(
            f"/api/v1/projects/{project_id}/brainstorm/finalize",
            headers=auth_headers,
        )
        assert finalize_response.status_code == 200
        finalize_data = finalize_response.json()["data"]
        assert finalize_data["status"] == "finalized"

        project_response = await async_client.get(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )
        assert project_response.status_code == 200
        project_data = project_response.json()["data"]
        assert project_data["status"] == "planning"
        assert "Clarified decisions:" in project_data["prd_content"]


@pytest.mark.integration
class TestPipelinePhaseApprovals:
    """Tests for human approval decisions on pipeline phases."""

    async def test_approve_waiting_phase_marks_it_completed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Approving a waiting phase completes it and records the approver."""
        project_id = await _create_brainstorm_project(async_client, auth_headers)
        pipeline_response = await async_client.post(
            f"/api/v1/projects/{project_id}/pipelines",
            json={"mode": "review_only"},
            headers=auth_headers,
        )
        assert pipeline_response.status_code == 201
        pipeline_id = pipeline_response.json()["data"]["id"]

        phases_response = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}/phases",
            headers=auth_headers,
        )
        assert phases_response.status_code == 200
        phase = phases_response.json()["data"][0]

        phase_row = await test_db_session.scalar(
            select(PipelinePhase).where(PipelinePhase.id == phase["id"])
        )
        assert phase_row is not None
        phase_row.status = PhaseStatus.WAITING_APPROVAL
        phase_row.requires_approval = True
        await test_db_session.commit()

        test_db_phase_response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/phases/{phase['id']}/approve",
            json={"approved": True, "comment": "Looks ready."},
            headers=auth_headers,
        )

        assert test_db_phase_response.status_code == 200
        updated = test_db_phase_response.json()["data"]
        assert updated["status"] == "completed"
        assert updated["approved_by"] == "testuser@example.com"
        assert updated["error_message"] is None

    async def test_reject_waiting_phase_marks_pipeline_failed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_db_session: AsyncSession,
    ) -> None:
        """Rejecting a waiting phase fails that phase and bubbles an error to the pipeline."""
        project_id = await _create_brainstorm_project(async_client, auth_headers)
        pipeline_response = await async_client.post(
            f"/api/v1/projects/{project_id}/pipelines",
            json={"mode": "review_only"},
            headers=auth_headers,
        )
        assert pipeline_response.status_code == 201
        pipeline_id = pipeline_response.json()["data"]["id"]

        phases_response = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}/phases",
            headers=auth_headers,
        )
        assert phases_response.status_code == 200
        phase = phases_response.json()["data"][0]

        phase_row = await test_db_session.scalar(
            select(PipelinePhase).where(PipelinePhase.id == phase["id"])
        )
        assert phase_row is not None
        phase_row.status = PhaseStatus.WAITING_APPROVAL
        phase_row.requires_approval = True
        await test_db_session.commit()

        rejection_response = await async_client.post(
            f"/api/v1/pipelines/{pipeline_id}/phases/{phase['id']}/approve",
            json={"approved": False, "comment": "Architecture needs another pass."},
            headers=auth_headers,
        )

        assert rejection_response.status_code == 200
        updated = rejection_response.json()["data"]
        assert updated["status"] == "failed"
        assert updated["error_message"] == "Architecture needs another pass."

        pipeline_detail = await async_client.get(
            f"/api/v1/pipelines/{pipeline_id}",
            headers=auth_headers,
        )
        assert pipeline_detail.status_code == 200
        assert pipeline_detail.json()["data"]["status"] == "failed"
        assert (
            pipeline_detail.json()["data"]["error_message"]
            == "Architecture needs another pass."
        )