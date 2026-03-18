"""SQLAlchemy DeclarativeBase with shared mixins."""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all CodeBot ORM models.

    Provides a ``type_annotation_map`` so Mapped[uuid.UUID] and
    Mapped[datetime] columns are stored using the correct SA types.
    """

    type_annotation_map: dict[type, Any] = {
        uuid.UUID: sa.Uuid,
        datetime: sa.DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` timestamp columns.

    ``created_at`` is set automatically by the DB on INSERT.
    ``updated_at`` is refreshed by the DB on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
