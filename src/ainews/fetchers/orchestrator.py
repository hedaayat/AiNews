"""Fetch orchestrator for coordinating multiple fetchers."""

import asyncio
from datetime import date

from ainews.config import Settings
from ainews.fetchers.base import BaseFetcher
from ainews.fetchers.rss import RSSFetcher
from ainews.fetchers.scraper import WebScraper
from ainews.models.article import Article
from ainews.models.source import Source
from ainews.processing.dedup import Deduplicator
from ainews.sources.manager import SourceManager
from ainews.storage.json_store import DatePartitionedStore


class FetchOrchestrator:
    """Coordinates fetching from multiple sources."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.fetchers: list[BaseFetcher] = [
            RSSFetcher(timeout=settings.fetch_timeout, user_agent=settings.user_agent),
            WebScraper(timeout=settings.fetch_timeout, user_agent=settings.user_agent),
        ]
        self.source_manager = SourceManager(settings.sources_file)
        self.article_store = DatePartitionedStore(settings.articles_dir, Article)
        self.deduplicator = Deduplicator()

    def _get_fetcher(self, source: Source) -> BaseFetcher | None:
        """Get the appropriate fetcher for a source."""
        for fetcher in self.fetchers:
            if fetcher.can_handle(source):
                return fetcher
        return None

    async def fetch_source(self, source: Source) -> list[Article]:
        """Fetch articles from a single source."""
        fetcher = self._get_fetcher(source)
        if not fetcher:
            print(f"No fetcher available for source type: {source.source_type}")
            return []

        articles = await fetcher.fetch(source)
        return articles

    async def fetch_all(
        self,
        sources: list[Source] | None = None,
        force: bool = False,
    ) -> list[Article]:
        """Fetch articles from all sources concurrently.

        Args:
            sources: Specific sources to fetch. If None, fetches all due sources.
            force: If True, fetches regardless of last_fetched time.

        Returns:
            List of all fetched articles (deduplicated).
        """
        if sources is None:
            if force:
                sources = self.source_manager.list_sources(enabled_only=True)
            else:
                sources = self.source_manager.get_sources_to_fetch()

        if not sources:
            print("No sources to fetch")
            return []

        # Create semaphore to limit concurrent fetches
        semaphore = asyncio.Semaphore(self.settings.max_concurrent_fetches)

        async def fetch_with_semaphore(source: Source) -> list[Article]:
            async with semaphore:
                articles = await self.fetch_source(source)
                # Mark source as fetched
                self.source_manager.mark_fetched(source.id)
                return articles

        # Fetch all sources concurrently
        tasks = [fetch_with_semaphore(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results and filter out exceptions
        all_articles: list[Article] = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                print(f"Fetch error: {result}")

        # Load existing articles for today to deduplicate against
        today = date.today()
        existing_articles = self.article_store.load(today)

        # Deduplicate
        new_articles = self.deduplicator.deduplicate(all_articles, existing_articles)

        # Save new articles
        if new_articles:
            all_today = existing_articles + new_articles
            self.article_store.save(today, all_today)

        return new_articles

    async def fetch_single(self, source_id: str) -> list[Article]:
        """Fetch articles from a single source by ID."""
        source = self.source_manager.get_source(source_id)
        if not source:
            print(f"Source not found: {source_id}")
            return []

        return await self.fetch_all(sources=[source], force=True)
