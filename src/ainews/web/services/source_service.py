"""Service for handling sources."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ainews.db.models import Source


class SourceService:
    """Service for source operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def get_all_sources(self) -> list[Source]:
        """Get all enabled sources."""
        stmt = select(Source).where(Source.enabled == True).order_by(Source.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_source_by_id(self, source_id: str) -> Optional[Source]:
        """Get a specific source."""
        stmt = select(Source).where(Source.id == source_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sources_by_tag(self, tag: str) -> list[Source]:
        """Get sources by tag."""
        # PostgreSQL array contains operator
        stmt = (
            select(Source)
            .where(Source.enabled == True)
            .where(Source.tags.contains([tag]))
            .order_by(Source.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
