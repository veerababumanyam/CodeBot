"""Standard response envelope models for the CodeBot API.

All API responses are wrapped in a consistent envelope structure providing
a ``status`` field, metadata (request ID, timestamp), and either ``data``
or ``error`` payloads.
"""

from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    """Response metadata included in every API response."""

    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    page: int
    per_page: int
    total: int
    total_pages: int


class ResponseEnvelope(BaseModel, Generic[T]):  # noqa: UP046
    """Standard success response wrapper."""

    status: str = "success"
    data: T
    meta: Meta = Field(default_factory=Meta)


class PaginatedEnvelope(BaseModel, Generic[T]):  # noqa: UP046
    """Paginated success response wrapper for list endpoints."""

    status: str = "success"
    data: list[T]
    meta: Meta = Field(default_factory=Meta)
    pagination: PaginationMeta | None = None


class ErrorDetail(BaseModel):
    """Structured error information."""

    code: str
    message: str
    details: list[dict] | None = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    status: str = "error"
    error: ErrorDetail
    meta: Meta = Field(default_factory=Meta)
