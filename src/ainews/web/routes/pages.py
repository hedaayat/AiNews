"""HTML page routes for AiNews."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from ainews.web.dependencies import get_db_session
from ainews.web.services.summary_service import SummaryService
from ainews.web.services.article_service import ArticleService
from ainews.web.services.source_service import SourceService

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Homepage showing today's summary."""
    summary_service = SummaryService(session)
    summary = await summary_service.get_latest_summary()

    context = {
        "request": request,
        "title": "Today's AI News",
        "summary": summary,
    }

    return templates.TemplateResponse("home.html", context)


@router.get("/archive", response_class=HTMLResponse)
async def archive(request: Request, session: AsyncSession = Depends(get_db_session)):
    """Archive of past summaries."""
    summary_service = SummaryService(session)
    dates = await summary_service.get_summary_dates(limit=365)

    context = {
        "request": request,
        "title": "Archive",
        "dates": dates,
    }

    return templates.TemplateResponse("archive.html", context)


@router.get("/archive/{date}", response_class=HTMLResponse)
async def archive_date(date: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    """View summary for a specific date."""
    summary_service = SummaryService(session)
    summary = await summary_service.get_summary_by_date(date)

    context = {
        "request": request,
        "date": date,
        "title": f"Summary - {date}",
        "summary": summary,
    }

    return templates.TemplateResponse("summary_detail.html", context)


@router.get("/articles", response_class=HTMLResponse)
async def articles(
    request: Request,
    date: str = None,
    source_id: str = None,
    page: int = 1,
    session: AsyncSession = Depends(get_db_session),
):
    """Browse all articles with optional filtering."""
    article_service = ArticleService(session)
    source_service = SourceService(session)

    limit = 20
    offset = (page - 1) * limit

    if source_id:
        articles_list, total = await article_service.get_articles_by_source(
            source_id, limit=limit, offset=offset
        )
    elif date:
        articles_list, total = await article_service.get_articles_by_date(
            date, limit=limit, offset=offset
        )
    else:
        articles_list = []
        total = 0

    sources = await source_service.get_all_sources()
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    context = {
        "request": request,
        "title": "Articles",
        "articles": articles_list,
        "sources": sources,
        "current_date": date,
        "current_source": source_id,
        "page": page,
        "total": total,
        "total_pages": total_pages,
        "limit": limit,
    }

    return templates.TemplateResponse("articles.html", context)


@router.get("/sources", response_class=HTMLResponse)
async def sources(request: Request, session: AsyncSession = Depends(get_db_session)):
    """View all news sources."""
    source_service = SourceService(session)
    sources_list = await source_service.get_all_sources()

    context = {
        "request": request,
        "title": "Sources",
        "sources": sources_list,
    }

    return templates.TemplateResponse("sources.html", context)
