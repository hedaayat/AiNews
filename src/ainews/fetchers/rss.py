"""RSS/Atom feed fetcher."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from ainews.fetchers.base import BaseFetcher
from ainews.models.article import Article
from ainews.models.source import Source, SourceType


class RSSFetcher(BaseFetcher):
    """Fetcher for RSS and Atom feeds."""

    def __init__(self, timeout: int = 30, user_agent: str = "AiNews/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    def can_handle(self, source: Source) -> bool:
        """Check if this fetcher can handle RSS/Atom sources."""
        return source.source_type in (SourceType.RSS, SourceType.ATOM)

    async def fetch(self, source: Source) -> list[Article]:
        """Fetch articles from an RSS/Atom feed."""
        try:
            # Fetch the feed content
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    str(source.url),
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                response.raise_for_status()
                content = response.text

            # Parse the feed
            feed = feedparser.parse(content)

            articles = []
            for entry in feed.entries:
                article = self._parse_entry(entry, source)
                if article:
                    articles.append(article)

            return articles

        except Exception as e:
            # Log error but don't crash - return empty list
            print(f"Error fetching {source.name}: {e}")
            return []

    def _parse_entry(self, entry: Any, source: Source) -> Article | None:
        """Parse a feed entry into an Article."""
        try:
            # Get URL - required
            url = entry.get("link") or entry.get("id")
            if not url:
                return None

            # Get title - required
            title = entry.get("title", "").strip()
            if not title:
                return None

            # Get content
            content = self._extract_content(entry)

            # Get publication date
            published_at = self._parse_date(entry)

            # Create article
            article = Article(
                id=Article.generate_id(url),
                title=title,
                url=url,
                source_id=source.id,
                published_at=published_at,
                fetched_at=datetime.utcnow(),
                content=content,
                content_hash=Article.generate_content_hash(content) if content else "",
                tags=self._extract_tags(entry),
            )

            return article

        except Exception:
            return None

    def _extract_content(self, entry: Any) -> str:
        """Extract the best available content from an entry."""
        # Try content first (full article)
        if "content" in entry:
            for content in entry.content:
                if content.get("type", "").startswith("text"):
                    return self._clean_html(content.get("value", ""))

        # Try summary/description
        summary = entry.get("summary") or entry.get("description", "")
        if summary:
            return self._clean_html(summary)

        return ""

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and clean up text."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator=" ", strip=True)
        # Normalize whitespace
        return " ".join(text.split())

    def _parse_date(self, entry: Any) -> datetime | None:
        """Parse publication date from entry."""
        # Try different date fields
        for field in ["published", "updated", "created"]:
            date_str = entry.get(f"{field}_parsed")
            if date_str:
                try:
                    return datetime(*date_str[:6])
                except Exception:
                    pass

            date_str = entry.get(field)
            if date_str:
                try:
                    return parsedate_to_datetime(date_str)
                except Exception:
                    pass

        return None

    def _extract_tags(self, entry: Any) -> list[str]:
        """Extract tags/categories from entry."""
        tags = []
        if "tags" in entry:
            for tag in entry.tags:
                term = tag.get("term") or tag.get("label")
                if term:
                    tags.append(term.lower())
        return tags
