"""Project CRUD endpoints for the CodeBot API."""

import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.deps import get_current_user, get_db, require_role
from codebot.api.envelope import PaginatedEnvelope, PaginationMeta, ResponseEnvelope
from codebot.api.schemas.projects import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectResponse,
    ProjectUpdate,
)
from codebot.db.models.user import User
from codebot.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_project_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectService:
    """Dependency that provides a ProjectService instance."""
    return ProjectService(db)


@router.post(
    "",
    response_model=ResponseEnvelope[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[ProjectService, Depends(_get_project_service)],
) -> ResponseEnvelope[ProjectResponse]:
    """Create a new project.

    Requires user or admin role. Viewers cannot create projects.

    Args:
        body: Project creation data.
        current_user: The authenticated user (must be user or admin role).
        service: Project service dependency.

    Returns:
        Created project wrapped in response envelope.
    """
    project = await service.create(payload=body, owner=current_user)
    return ResponseEnvelope(data=ProjectResponse.model_validate(project))


@router.get(
    "",
    response_model=PaginatedEnvelope[ProjectResponse],
)
async def list_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(_get_project_service)],
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
) -> PaginatedEnvelope[ProjectResponse]:
    """List projects for the authenticated user.

    Supports optional filtering by status and name search.

    Args:
        current_user: The authenticated user.
        service: Project service dependency.
        page: Page number (1-based).
        per_page: Items per page (1-100).
        status_filter: Optional status filter.
        search: Optional name search (ilike).

    Returns:
        Paginated list of projects.
    """
    projects, total = await service.list_for_user(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        status=status_filter,
        search=search,
    )
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    return PaginatedEnvelope(
        data=[ProjectResponse.model_validate(p) for p in projects],
        pagination=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{project_id}",
    response_model=ResponseEnvelope[ProjectDetailResponse],
)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(_get_project_service)],
) -> ResponseEnvelope[ProjectDetailResponse]:
    """Get a project by ID with full detail.

    Returns 404 if not found or not owned by the current user.

    Args:
        project_id: The project UUID.
        current_user: The authenticated user.
        service: Project service dependency.

    Returns:
        Project detail wrapped in response envelope.
    """
    project = await service.get(project_id)
    if project is None or (
        project.user_id != current_user.id and current_user.role.value.lower() != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return ResponseEnvelope(data=ProjectDetailResponse.model_validate(project))


@router.patch(
    "/{project_id}",
    response_model=ResponseEnvelope[ProjectResponse],
)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[ProjectService, Depends(_get_project_service)],
) -> ResponseEnvelope[ProjectResponse]:
    """Update a project's name or description.

    Args:
        project_id: The project UUID.
        body: Fields to update.
        current_user: The authenticated user (must be user or admin role).
        service: Project service dependency.

    Returns:
        Updated project wrapped in response envelope.
    """
    project = await service.get(project_id)
    if project is None or (
        project.user_id != current_user.id and current_user.role.value.lower() != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    updated = await service.update(project, body)
    return ResponseEnvelope(data=ProjectResponse.model_validate(updated))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(require_role("user", "admin"))],
    service: Annotated[ProjectService, Depends(_get_project_service)],
) -> Response:
    """Delete a project.

    Args:
        project_id: The project UUID.
        current_user: The authenticated user (must be user or admin role).
        service: Project service dependency.

    Returns:
        204 No Content.
    """
    project = await service.get(project_id)
    if project is None or (
        project.user_id != current_user.id and current_user.role.value.lower() != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    await service.delete(project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
