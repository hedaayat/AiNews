"""Service for handling articles."""
from datetime import datetime, date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, cast, Date

from ainews.db.models import Article


class ArticleService:
    """Service for article operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def get_articles_by_date(
        self, date_str: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Article], int]:
        """Get articles for a specific date with pagination."""
        try:
            article_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return [], 0

        # Build query to find articles fetched on this date
        stmt_count = select(func.count(Article.id)).where(
            cast(Article.fetched_at, Date) == article_date
        )
        count_result = await self.session.execute(stmt_count)
        total = count_result.scalar() or 0

        stmt = (
            select(Article)
            .where(cast(Article.fetched_at, Date) == article_date)
            .order_by(desc(Article.published_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        articles = result.scalars().all()
        return articles, total

    async def get_articles_by_source(
        self, source_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Article], int]:
        """Get articles from a specific source with pagination."""
        stmt_count = select(func.count(Article.id)).where(Article.source_id == source_id)
        count_result = await self.session.execute(stmt_count)
        total = count_result.scalar() or 0

        stmt = (
            select(Article)
            .where(Article.source_id == source_id)
            .order_by(desc(Article.published_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        articles = result.scalars().all()
        return articles, total

    async def search_articles(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[Article], int]:
        """Search articles by title or content (basic search for Phase 1)."""
        search_pattern = f"%{query}%"

        stmt_count = select(func.count(Article.id)).where(
            Article.title.ilike(search_pattern) | Article.content.ilike(search_pattern)
        )
        count_result = await self.session.execute(stmt_count)
        total = count_result.scalar() or 0

        stmt = (
            select(Article)
            .where(Article.title.ilike(search_pattern) | Article.content.ilike(search_pattern))
            .order_by(desc(Article.published_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        articles = result.scalars().all()
        return articles, total
