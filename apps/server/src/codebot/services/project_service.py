"""Project service handling CRUD operations for CodeBot projects."""

from __future__ import annotations

import base64
import binascii
import io
import re
import zipfile
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import urlopen
from uuid import UUID

from fastapi import HTTPException, status
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.api.schemas.projects import ProjectCreate, ProjectUpdate
from codebot.db.models.project import Project, ProjectStatus, ProjectType
from codebot.db.models.user import User
from codebot.pipeline.project_detector import detect_project_type


class _HTMLTextExtractor(HTMLParser):
    """Very small HTML-to-text helper for URL-imported PRDs."""

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self._chunks.append(stripped)

    def get_text(self) -> str:
        return "\n".join(self._chunks)


def _extract_docx_text(raw_bytes: bytes) -> str:
    """Extract rough text content from a DOCX payload using stdlib only."""
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", document_xml)
    return re.sub(r"\s+", " ", text).strip()


def _extract_pdf_text(raw_bytes: bytes) -> str:
    """Extract text content from a PDF payload."""
    reader = PdfReader(io.BytesIO(raw_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return re.sub(r"\s+", " ", text).strip()


def _decode_file_payload(payload: str) -> tuple[str | None, bytes]:
    """Decode a plain base64 or data URL payload into raw bytes."""
    media_type: str | None = None
    encoded = payload
    if payload.startswith("data:"):
        header, encoded = payload.split(",", 1)
        media_type = header[5:].split(";", 1)[0] or None
    try:
        return media_type, base64.b64decode(encoded)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid base64 file payload",
        ) from exc


def _extract_text_from_file(
    *,
    payload: str,
    source_name: str | None,
    source_media_type: str | None,
) -> str:
    """Extract normalized text from an uploaded project document."""
    inferred_media_type, raw_bytes = _decode_file_payload(payload)
    media_type = (source_media_type or inferred_media_type or "").lower()
    filename = (source_name or "uploaded-document").lower()

    if media_type.startswith("text/") or filename.endswith((".md", ".markdown", ".txt")):
        return raw_bytes.decode("utf-8", errors="ignore").strip()

    if (
        media_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or filename.endswith(".docx")
    ):
        try:
            return _extract_docx_text(raw_bytes)
        except (KeyError, zipfile.BadZipFile) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to extract text from DOCX upload",
            ) from exc

    if media_type == "application/pdf" or filename.endswith(".pdf"):
        try:
            text = _extract_pdf_text(raw_bytes)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to extract text from PDF upload",
            ) from exc

        if text:
            return text

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded PDF does not contain extractable text",
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Unsupported uploaded document type. Supported: .md, .txt, .docx, .pdf.",
    )


def _extract_text_from_url(url: str) -> str:
    """Fetch a remote PRD and normalize it into plain text."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="prd_url must use http or https",
        )

    try:
        with urlopen(url, timeout=10) as response:  # noqa: S310
            content_type = (response.headers.get_content_type() or "text/plain").lower()
            raw_bytes = response.read()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to fetch PRD from the provided URL",
        ) from exc

    text = raw_bytes.decode("utf-8", errors="ignore")
    if "html" in content_type:
        parser = _HTMLTextExtractor()
        parser.feed(text)
        return parser.get_text().strip()
    return text.strip()


def _normalize_project_type(value: str | None, repository_path: str, prd_content: str) -> ProjectType:
    """Resolve explicit or detected project type into the ORM enum."""
    if value is not None:
        return ProjectType(value.upper())
    detected = detect_project_type(repository_path=repository_path, prd_content=prd_content)
    return ProjectType(detected.value)


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
            "url": "markdown",
            "file": "markdown",
        }
        prd_format = format_map.get(payload.prd_source, "markdown")

        prd_content = payload.prd_content.strip()
        if payload.prd_source == "url" and payload.prd_url is not None:
            prd_content = _extract_text_from_url(payload.prd_url)
        elif payload.prd_source == "file" and payload.prd_file is not None:
            prd_content = _extract_text_from_file(
                payload=payload.prd_file,
                source_name=payload.source_name,
                source_media_type=payload.source_media_type,
            )

        repository_path = (payload.repository_path or "").strip()
        repository_url = payload.repository_url.strip() if payload.repository_url else None
        project_type = _normalize_project_type(
            value=payload.project_type,
            repository_path=repository_path,
            prd_content=prd_content,
        )

        project = Project(
            user_id=owner.id,
            name=payload.name,
            description=payload.description,
            status=(
                ProjectStatus.BRAINSTORMING
                if (payload.settings or {}).get("kickoff_flow") == "brainstorm"
                else ProjectStatus.CREATED
            ),
            project_type=project_type,
            prd_content=prd_content,
            prd_format=prd_format,
            tech_stack=payload.tech_stack,
            repository_path=repository_path,
            repository_url=repository_url,
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
        return await self._db.get(Project, project_id, populate_existing=True)

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
