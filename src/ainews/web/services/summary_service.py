"""Service for handling summaries."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from ainews.db.models import Summary, NotableStory


class SummaryService:
    """Service for summary operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def get_latest_summary(self) -> Optional[Summary]:
        """Get today's summary (most recent summary)."""
        stmt = select(Summary).order_by(desc(Summary.date)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_summary_by_date(self, date_str: str) -> Optional[Summary]:
        """Get summary for a specific date (YYYY-MM-DD format)."""
        stmt = select(Summary).where(Summary.date == date_str)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_summary_dates(self, limit: int = 30) -> list[str]:
        """Get list of available summary dates (most recent first)."""
        stmt = select(Summary.date).order_by(desc(Summary.date)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
