"""Dependency injection for FastAPI routes."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ainews.db.session import get_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async for session in get_session():
        yield session
