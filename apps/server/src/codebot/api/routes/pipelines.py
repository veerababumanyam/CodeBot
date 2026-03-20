"""Pipeline CRUD and lifecycle endpoints for the CodeBot API."""

import math
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.deps import get_current_user, get_db, require_role
from codebot.api.envelope import PaginatedEnvelope, PaginationMeta, ResponseEnvelope
from codebot.api.schemas.pipelines import (
    PhaseApprovalRequest,
    PipelineActionResponse,
    PipelineCreate,
    PipelineDetailResponse,
    PipelinePhaseResponse,
    PipelineResponse,
)
from codebot.db.models.project import PipelineStatus
from codebot.db.models.user import User
from codebot.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])
project_pipelines_router = APIRouter(prefix="/projects", tags=["pipelines"])


def _get_pipeline_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PipelineService:
    """Dependency that provides a PipelineService instance."""
    return PipelineService(db)


# ---------------------------------------------------------------------------
# Project-scoped pipeline endpoints (nested under /projects/{project_id})
# ---------------------------------------------------------------------------


@project_pipelines_router.post(
    "/{project_id}/pipelines",
    response_model=ResponseEnvelope[PipelineResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_pipeline(
    project_id: UUID,
    body: PipelineCreate,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelineResponse]:
    """Create a new pipeline for a project.

    Args:
        project_id: The project UUID.
        body: Pipeline creation data (mode, phases, config).
        current_user: Authenticated user (user or admin role).
        service: Pipeline service dependency.

    Returns:
        Created pipeline wrapped in response envelope.
    """
    pipeline = await service.create(project_id, body)
    return ResponseEnvelope(data=PipelineResponse.model_validate(pipeline))


@project_pipelines_router.get(
    "/{project_id}/pipelines",
    response_model=PaginatedEnvelope[PipelineResponse],
)
async def list_pipelines(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> PaginatedEnvelope[PipelineResponse]:
    """List pipelines for a project.

    Args:
        project_id: The project UUID.
        current_user: Authenticated user.
        service: Pipeline service dependency.
        page: Page number (1-based).
        per_page: Items per page.
        status_filter: Optional status filter.

    Returns:
        Paginated list of pipelines.
    """
    pipelines, total = await service.list_for_project(
        project_id, page=page, per_page=per_page, status=status_filter
    )
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    return PaginatedEnvelope(
        data=[PipelineResponse.model_validate(p) for p in pipelines],
        pagination=PaginationMeta(
            page=page, per_page=per_page, total=total, total_pages=total_pages
        ),
    )


# ---------------------------------------------------------------------------
# Pipeline-level endpoints (direct /pipelines/{pipeline_id})
# ---------------------------------------------------------------------------


@router.get(
    "/{pipeline_id}",
    response_model=ResponseEnvelope[PipelineDetailResponse],
)
async def get_pipeline(
    pipeline_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelineDetailResponse]:
    """Get a pipeline by ID with full detail.

    Args:
        pipeline_id: The pipeline UUID.
        current_user: Authenticated user.
        service: Pipeline service dependency.

    Returns:
        Pipeline detail wrapped in response envelope.
    """
    pipeline = await service.get_with_phases(pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    return ResponseEnvelope(data=PipelineDetailResponse.model_validate(pipeline))


@router.post(
    "/{pipeline_id}/start",
    response_model=ResponseEnvelope[PipelineActionResponse],
)
async def start_pipeline(
    pipeline_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelineActionResponse]:
    """Start a pipeline (transition from PENDING to RUNNING).

    Args:
        pipeline_id: The pipeline UUID.
        current_user: Authenticated user (user or admin role).
        service: Pipeline service dependency.

    Returns:
        Pipeline action response.
    """
    pipeline = await service.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    updated = await service.transition(pipeline, PipelineStatus.RUNNING)
    return ResponseEnvelope(
        data=PipelineActionResponse(
            id=updated.id,
            status=updated.status.value.lower(),
            timestamp=datetime.now(UTC),
        )
    )


@router.post(
    "/{pipeline_id}/pause",
    response_model=ResponseEnvelope[PipelineActionResponse],
)
async def pause_pipeline(
    pipeline_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelineActionResponse]:
    """Pause a running pipeline.

    Args:
        pipeline_id: The pipeline UUID.
        current_user: Authenticated user.
        service: Pipeline service dependency.

    Returns:
        Pipeline action response.
    """
    pipeline = await service.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    updated = await service.transition(pipeline, PipelineStatus.PAUSED)
    return ResponseEnvelope(
        data=PipelineActionResponse(
            id=updated.id,
            status=updated.status.value.lower(),
            timestamp=datetime.now(UTC),
        )
    )


@router.post(
    "/{pipeline_id}/resume",
    response_model=ResponseEnvelope[PipelineActionResponse],
)
async def resume_pipeline(
    pipeline_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelineActionResponse]:
    """Resume a paused pipeline.

    Args:
        pipeline_id: The pipeline UUID.
        current_user: Authenticated user.
        service: Pipeline service dependency.

    Returns:
        Pipeline action response.
    """
    pipeline = await service.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    updated = await service.transition(pipeline, PipelineStatus.RUNNING)
    return ResponseEnvelope(
        data=PipelineActionResponse(
            id=updated.id,
            status=updated.status.value.lower(),
            timestamp=datetime.now(UTC),
        )
    )


@router.post(
    "/{pipeline_id}/cancel",
    response_model=ResponseEnvelope[PipelineActionResponse],
)
async def cancel_pipeline(
    pipeline_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelineActionResponse]:
    """Cancel a pipeline.

    Args:
        pipeline_id: The pipeline UUID.
        current_user: Authenticated user.
        service: Pipeline service dependency.

    Returns:
        Pipeline action response.
    """
    pipeline = await service.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    updated = await service.transition(pipeline, PipelineStatus.CANCELLED)
    return ResponseEnvelope(
        data=PipelineActionResponse(
            id=updated.id,
            status=updated.status.value.lower(),
            timestamp=datetime.now(UTC),
        )
    )


@router.get(
    "/{pipeline_id}/phases",
    response_model=ResponseEnvelope[list[PipelinePhaseResponse]],
)
async def get_pipeline_phases(
    pipeline_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[list[PipelinePhaseResponse]]:
    """Get all phases of a pipeline.

    Args:
        pipeline_id: The pipeline UUID.
        current_user: Authenticated user.
        service: Pipeline service dependency.

    Returns:
        Ordered list of pipeline phases.
    """
    phases = await service.get_phases(pipeline_id)
    return ResponseEnvelope(
        data=[PipelinePhaseResponse.model_validate(p) for p in phases]
    )


@router.post(
    "/{pipeline_id}/phases/{phase_id}/approve",
    response_model=ResponseEnvelope[PipelinePhaseResponse],
)
async def approve_phase(
    pipeline_id: UUID,
    phase_id: UUID,
    body: PhaseApprovalRequest,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[PipelineService, Depends(_get_pipeline_service)],
) -> ResponseEnvelope[PipelinePhaseResponse]:
    """Approve or reject a pipeline phase.

    Args:
        pipeline_id: The pipeline UUID.
        phase_id: The phase UUID.
        body: Approval request data.
        current_user: Authenticated user (user or admin role).
        service: Pipeline service dependency.

    Returns:
        Updated phase wrapped in response envelope.
    """
    phases = await service.get_phases(pipeline_id)
    phase = next((p for p in phases if p.id == phase_id), None)
    if phase is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found"
        )
    updated = await service.approve_phase(
        phase,
        approved_by=current_user.email if hasattr(current_user, "email") else str(current_user.id),
        comment=body.comment,
    )
    return ResponseEnvelope(data=PipelinePhaseResponse.model_validate(updated))
