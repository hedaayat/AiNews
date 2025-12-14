"""Base fetcher interface."""

from abc import ABC, abstractmethod

from ainews.models.article import Article
from ainews.models.source import Source


class BaseFetcher(ABC):
    """Abstract base class for news fetchers."""

    @abstractmethod
    async def fetch(self, source: Source) -> list[Article]:
        """Fetch articles from a source.

        Args:
            source: The source to fetch from.

        Returns:
            List of fetched articles.
        """
        pass

    @abstractmethod
    def can_handle(self, source: Source) -> bool:
        """Check if this fetcher can handle the given source.

        Args:
            source: The source to check.

        Returns:
            True if this fetcher can handle the source.
        """
        pass
