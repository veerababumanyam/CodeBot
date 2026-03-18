"""Shared pytest fixtures for the codebot-server test suite."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from codebot.config import settings


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional AsyncSession that rolls back after each test.

    Creates a fresh engine per test function so there are no cross-loop issues
    when asyncio_default_fixture_loop_scope is "function".  Each session wraps
    the test in a SAVEPOINT so inserts/updates are never committed to the DB.
    """
    engine = create_async_engine(settings.database_url, echo=False, pool_size=1, max_overflow=0)
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with factory() as session:
        async with session.begin_nested():
            yield session
        await session.rollback()
    await engine.dispose()
