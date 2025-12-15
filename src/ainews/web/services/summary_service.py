"""Service for handling summaries."""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ainews.db.models import Summary, NotableStory


class SummaryService:
    """Service for summary operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def get_latest_summary(self) -> Summary | None:
        """Get today's summary."""
        # TODO: Implement
        pass

    async def get_summary_by_date(self, date_str: str) -> Summary | None:
        """Get summary for a specific date."""
        # TODO: Implement
        pass

    async def get_summary_dates(self, limit: int = 30) -> list[str]:
        """Get list of available summary dates."""
        # TODO: Implement
        pass
