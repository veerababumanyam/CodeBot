"""Project service handling CRUD operations for CodeBot projects."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.schemas.projects import ProjectCreate, ProjectUpdate
from codebot.db.models.project import Project, ProjectStatus
from codebot.db.models.user import User


class ProjectService:
    """Business logic for project operations.

    Args:
        db: Async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: ProjectCreate, owner: User) -> Project:
        """Create a new project.

        Args:
            payload: Project creation data.
            owner: The user who owns the project.

        Returns:
            The created Project ORM object.
        """
        # Map prd_source to prd_format
        format_map = {
            "text": "markdown",
            "markdown": "markdown",
            "json": "json",
            "yaml": "yaml",
        }
        prd_format = format_map.get(payload.prd_source, "markdown")

        project = Project(
            user_id=owner.id,
            name=payload.name,
            description=payload.description,
            prd_content=payload.prd_content,
            prd_format=prd_format,
            tech_stack=payload.tech_stack,
            config=payload.settings,
        )
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Project], int]:
        """List projects belonging to a user with optional filters.

        Args:
            user_id: The owning user's UUID.
            page: Page number (1-based).
            per_page: Items per page.
            status: Optional status filter (case-insensitive).
            search: Optional name search filter (ilike).

        Returns:
            Tuple of (projects list, total count).
        """
        query = select(Project).where(Project.user_id == user_id)
        count_query = select(func.count()).select_from(Project).where(Project.user_id == user_id)

        if status is not None:
            try:
                status_enum = ProjectStatus(status.upper())
            except ValueError:
                status_enum = None
            if status_enum is not None:
                query = query.where(Project.status == status_enum)
                count_query = count_query.where(Project.status == status_enum)

        if search is not None:
            query = query.where(Project.name.ilike(f"%{search}%"))
            count_query = count_query.where(Project.name.ilike(f"%{search}%"))

        # Total count
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(Project.created_at.desc())
        result = await self._db.execute(query)
        projects = list(result.scalars().all())

        return projects, int(total)

    async def get(self, project_id: UUID) -> Project | None:
        """Get a project by ID.

        Args:
            project_id: The project's UUID.

        Returns:
            The Project if found, else None.
        """
        return await self._db.get(Project, project_id)

    async def update(self, project: Project, payload: ProjectUpdate) -> Project:
        """Update a project with partial data.

        Args:
            project: The existing Project ORM object.
            payload: Fields to update (non-None values only).

        Returns:
            The updated Project ORM object.
        """
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(project, field, value)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        """Delete a project.

        Args:
            project: The Project ORM object to delete.
        """
        await self._db.delete(project)
        await self._db.commit()
