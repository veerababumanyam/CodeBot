"""Async SQLAlchemy engine and session factory for CodeBot."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from codebot.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    echo=settings.debug,
    future=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
