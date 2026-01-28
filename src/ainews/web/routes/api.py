"""API routes for AiNews."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ainews.web.dependencies import get_db_session
from ainews.web.services.summary_service import SummaryService
from ainews.web.services.article_service import ArticleService
from ainews.web.services.source_service import SourceService

router = APIRouter()


@router.get("/summaries/latest")
async def get_latest_summary(session: AsyncSession = Depends(get_db_session)):
    """Get today's summary (most recent)."""
    service = SummaryService(session)
    summary = await service.get_latest_summary()

    if not summary:
        raise HTTPException(status_code=404, detail="No summaries found")

    return {
        "date": summary.date,  # Already a string in YYYY-MM-DD format
        "summary": summary.summary_text,
        "key_topics": summary.key_topics,
        "article_count": summary.article_count,
        "generated_at": summary.generated_at.isoformat() if summary.generated_at else None,
    }


@router.get("/summaries/{date}")
async def get_summary_by_date(date: str, session: AsyncSession = Depends(get_db_session)):
    """Get summary for a specific date (YYYY-MM-DD format)."""
    service = SummaryService(session)
    summary = await service.get_summary_by_date(date)

    if not summary:
        raise HTTPException(status_code=404, detail=f"No summary found for date {date}")

    return {
        "date": summary.date,  # Already a string in YYYY-MM-DD format
        "summary": summary.summary_text,
        "key_topics": summary.key_topics,
        "article_count": summary.article_count,
        "generated_at": summary.generated_at.isoformat() if summary.generated_at else None,
    }


@router.get("/summaries")
async def list_summaries(
    limit: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    """Get list of available summary dates."""
    service = SummaryService(session)
    dates = await service.get_summary_dates(limit=limit)
    return {"dates": dates, "count": len(dates)}


@router.get("/articles")
async def get_articles(
    date: Optional[str] = None,
    source_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
):
    """Get articles, optionally filtered by date or source."""
    article_service = ArticleService(session)
    source_service = SourceService(session)

    if source_id:
        # Validate source exists
        source = await source_service.get_source_by_id(source_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

        articles, total = await article_service.get_articles_by_source(
            source_id, limit=limit, offset=offset
        )
    elif date:
        articles, total = await article_service.get_articles_by_date(
            date, limit=limit, offset=offset
        )
    else:
        # If no filters, get recent articles
        articles = []
        total = 0

    return {
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "url": a.url,
                "source_id": a.source_id,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "fetched_at": a.fetched_at.isoformat() if a.fetched_at else None,
                "word_count": a.word_count,
                "content": a.content[:500] if a.content else "",  # Summary
            }
            for a in articles
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/sources")
async def get_sources(session: AsyncSession = Depends(get_db_session)):
    """Get all enabled news sources."""
    service = SourceService(session)
    sources = await service.get_all_sources()

    return {
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "source_type": s.source_type,
                "tags": s.tags,
                "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
            }
            for s in sources
        ],
        "count": len(sources),
    }


@router.get("/sources/{source_id}")
async def get_source(source_id: str, session: AsyncSession = Depends(get_db_session)):
    """Get details of a specific source."""
    service = SourceService(session)
    source = await service.get_source_by_id(source_id)

    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    return {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "source_type": source.source_type,
        "enabled": source.enabled,
        "tags": source.tags,
        "last_fetched": source.last_fetched.isoformat() if source.last_fetched else None,
        "fetch_interval_hours": source.fetch_interval_hours,
    }
