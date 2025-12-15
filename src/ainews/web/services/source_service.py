"""Service for handling sources."""
from sqlalchemy.ext.asyncio import AsyncSession

from ainews.db.models import Source


class SourceService:
    """Service for source operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def get_all_sources(self) -> list[Source]:
        """Get all enabled sources."""
        # TODO: Implement
        pass

    async def get_source_by_id(self, source_id: str) -> Source | None:
        """Get a specific source."""
        # TODO: Implement
        pass

    async def get_sources_by_tag(self, tag: str) -> list[Source]:
        """Get sources by tag."""
        # TODO: Implement
        pass
