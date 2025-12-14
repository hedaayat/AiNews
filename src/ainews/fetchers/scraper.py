"""Web scraper fetcher."""

from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from ainews.fetchers.base import BaseFetcher
from ainews.models.article import Article
from ainews.models.source import Source, SourceType


class WebScraper(BaseFetcher):
    """Fetcher for web pages that need scraping."""

    def __init__(self, timeout: int = 30, user_agent: str = "AiNews/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    def can_handle(self, source: Source) -> bool:
        """Check if this fetcher can handle web scraping sources."""
        return source.source_type == SourceType.WEB

    async def fetch(self, source: Source) -> list[Article]:
        """Fetch articles by scraping a web page."""
        if not source.scrape_selector:
            print(f"No scrape_selector configured for {source.name}")
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    str(source.url),
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                response.raise_for_status()
                html = response.text

            soup = BeautifulSoup(html, "lxml")
            articles = []

            # Find article elements using the configured selector
            elements = soup.select(source.scrape_selector)

            for element in elements:
                article = self._parse_element(element, source)
                if article:
                    articles.append(article)

            return articles

        except Exception as e:
            print(f"Error scraping {source.name}: {e}")
            return []

    def _parse_element(self, element: BeautifulSoup, source: Source) -> Article | None:
        """Parse an HTML element into an Article."""
        try:
            # Try to find link
            link_elem = element.find("a", href=True)
            if not link_elem:
                return None

            url = link_elem.get("href", "")
            if not url:
                return None

            # Make URL absolute if relative
            if url.startswith("/"):
                from urllib.parse import urljoin

                url = urljoin(str(source.url), url)

            # Get title
            title = link_elem.get_text(strip=True)
            if not title:
                # Try to find a heading
                heading = element.find(["h1", "h2", "h3", "h4"])
                if heading:
                    title = heading.get_text(strip=True)

            if not title:
                return None

            # Get summary/description if available
            summary_elem = element.find(["p", "span", "div"], class_=lambda x: x and "summary" in x.lower() if x else False)
            content = ""
            if summary_elem:
                content = summary_elem.get_text(strip=True)
            else:
                # Try to get any paragraph text
                p_elem = element.find("p")
                if p_elem:
                    content = p_elem.get_text(strip=True)

            return Article(
                id=Article.generate_id(url),
                title=title,
                url=url,
                source_id=source.id,
                published_at=None,  # Hard to reliably extract from scraped pages
                fetched_at=datetime.utcnow(),
                content=content,
                content_hash=Article.generate_content_hash(content) if content else "",
                tags=source.tags,  # Use source tags
            )

        except Exception:
            return None
