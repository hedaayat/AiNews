"""API routes for AiNews."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ainews.web.dependencies import get_db_session

router = APIRouter()


@router.get("/summaries/latest")
async def get_latest_summary(session: AsyncSession = Depends(get_db_session)):
    """Get today's summary."""
    # TODO: Implement
    return {"message": "Latest summary endpoint - coming soon"}


@router.get("/summaries/{date}")
async def get_summary_by_date(date: str, session: AsyncSession = Depends(get_db_session)):
    """Get summary for a specific date (YYYY-MM-DD format)."""
    # TODO: Implement
    return {"date": date, "message": "Summary detail endpoint - coming soon"}


@router.get("/articles")
async def get_articles(
    date: str = None, source_id: str = None, session: AsyncSession = Depends(get_db_session)
):
    """Get articles, optionally filtered by date or source."""
    # TODO: Implement
    return {"message": "Articles endpoint - coming soon"}


@router.get("/sources")
async def get_sources(session: AsyncSession = Depends(get_db_session)):
    """Get all news sources."""
    # TODO: Implement
    return {"message": "Sources endpoint - coming soon"}
