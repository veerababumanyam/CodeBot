"""ORM model barrel — imports Base only initially; models added in Task 2b."""

from codebot.db.models.base import Base, TimestampMixin

__all__ = ["Base", "TimestampMixin"]
