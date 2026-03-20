"""Shared fixtures for API tests.

Uses a connection-scoped transaction + nested savepoints so that all
service-level ``commit()`` calls hit SAVEPOINTs instead of the real
transaction.  The outer transaction is rolled back after every test.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from codebot.api.deps import get_db
from codebot.auth.jwt import create_access_token
from codebot.config import settings
from codebot.db.models.user import User, UserRole
from codebot.main import fastapi_app
from codebot.services.auth_service import AuthService


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional AsyncSession with savepoint rollback.

    Every ``session.commit()`` inside service code actually commits a
    SAVEPOINT, and a new SAVEPOINT is immediately re-started.  At the
    end the outer BEGIN is rolled back so no data leaks between tests.
    """
    engine = create_async_engine(settings.database_url, echo=False, pool_size=1, max_overflow=0)
    conn = await engine.connect()
    trans = await conn.begin()

    session = AsyncSession(bind=conn, expire_on_commit=False)

    # Start a nested (SAVEPOINT) transaction
    await conn.begin_nested()

    # After each SAVEPOINT commit, immediately re-open a fresh one
    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(sync_session, sync_trans) -> None:  # type: ignore[no-untyped-def]
        if conn.closed:
            return
        if not conn.in_nested_transaction():
            conn.sync_connection.begin_nested()  # type: ignore[union-attr]

    yield session

    await session.close()
    await trans.rollback()
    await conn.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(
    test_db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient wired to the test FastAPI app.

    Overrides the ``get_db`` dependency to use the test session.
    """

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_token(test_db_session: AsyncSession) -> str:
    """Create a test user and return a valid JWT token."""
    service = AuthService(test_db_session)
    user = await service.register(
        email="testuser@example.com",
        password="securepassword123",
        name="Test User",
    )
    return create_access_token(user.id, user.role.value.lower())


@pytest_asyncio.fixture
async def auth_headers(test_user_token: str) -> dict[str, str]:
    """Return Authorization headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {test_user_token}"}
