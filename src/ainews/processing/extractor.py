"""Article content extraction."""

import httpx
import trafilatura


class ContentExtractor:
    """Extracts clean article content from web pages."""

    def __init__(self, timeout: int = 30, user_agent: str = "AiNews/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent

    async def extract_from_url(self, url: str) -> str | None:
        """Fetch and extract content from a URL.

        Args:
            url: The article URL to extract content from.

        Returns:
            Extracted text content, or None if extraction failed.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                response.raise_for_status()
                html = response.text

            return self.extract_from_html(html, url)

        except Exception as e:
            print(f"Error extracting from {url}: {e}")
            return None

    def extract_from_html(self, html: str, url: str | None = None) -> str | None:
        """Extract content from HTML.

        Args:
            html: The HTML content to extract from.
            url: Optional URL for better extraction accuracy.

        Returns:
            Extracted text content, or None if extraction failed.
        """
        try:
            # Use trafilatura for extraction
            content = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=False,
                no_fallback=False,
                favor_recall=True,
            )

            if content:
                # Clean up whitespace
                return " ".join(content.split())

            return None

        except Exception as e:
            print(f"Error extracting content: {e}")
            return None

    async def enrich_article(self, article: "Article") -> "Article":
        """Enrich an article with full content extraction.

        Args:
            article: Article with minimal content.

        Returns:
            Article with enriched content.
        """
        from ainews.models.article import Article as ArticleModel

        # Skip if already has substantial content
        if article.word_count > 200:
            return article

        # Extract full content
        content = await self.extract_from_url(str(article.url))
        if content and len(content) > len(article.content):
            article.update_content(content)

        return article
