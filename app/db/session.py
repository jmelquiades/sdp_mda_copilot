"""Database session and engine setup."""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Use a dedicated schema to avoid touching existing data
connect_args = {"server_settings": {"search_path": settings.db_schema}}

engine = create_async_engine(
    settings.database_url,
    echo=settings.sql_echo,
    connect_args=connect_args,
    future=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a database session for request-scoped usage."""
    async with SessionLocal() as session:
        yield session


async def check_database() -> None:
    """Run a lightweight DB check; raises on connection issues."""
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
