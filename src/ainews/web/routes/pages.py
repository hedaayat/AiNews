"""HTML page routes for AiNews."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage showing today's summary."""
    # TODO: Fetch today's summary from database
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "title": "Today's AI News"}
    )


@router.get("/archive", response_class=HTMLResponse)
async def archive(request: Request):
    """Archive of past summaries."""
    # TODO: Fetch list of available dates
    return templates.TemplateResponse(
        "archive.html",
        {"request": request, "title": "Archive"}
    )


@router.get("/archive/{date}", response_class=HTMLResponse)
async def archive_date(date: str, request: Request):
    """View summary for a specific date."""
    # TODO: Fetch summary for date
    return templates.TemplateResponse(
        "summary_detail.html",
        {"request": request, "date": date, "title": f"Summary - {date}"}
    )


@router.get("/articles", response_class=HTMLResponse)
async def articles(request: Request):
    """Browse all articles."""
    # TODO: Fetch articles with pagination
    return templates.TemplateResponse(
        "articles.html",
        {"request": request, "title": "Articles"}
    )


@router.get("/sources", response_class=HTMLResponse)
async def sources(request: Request):
    """View all news sources."""
    # TODO: Fetch sources
    return templates.TemplateResponse(
        "sources.html",
        {"request": request, "title": "Sources"}
    )
