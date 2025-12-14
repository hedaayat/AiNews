"""Source data model."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    """Type of news source."""

    RSS = "rss"
    ATOM = "atom"
    WEB = "web"  # For web scraping


class Source(BaseModel):
    """A news source configuration."""

    id: str = Field(description="Unique identifier (slug)")
    name: str = Field(description="Display name of the source")
    url: HttpUrl = Field(description="URL of the feed or page")
    source_type: SourceType = Field(default=SourceType.RSS, description="Type of source")
    enabled: bool = Field(default=True, description="Whether to fetch from this source")
    scrape_selector: Optional[str] = Field(
        default=None,
        description="CSS selector for web scraping (only for WEB type)",
    )
    last_fetched: Optional[datetime] = Field(
        default=None,
        description="Last successful fetch time",
    )
    fetch_interval_hours: int = Field(
        default=24,
        description="Minimum hours between fetches",
    )
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    discovered_by_ai: bool = Field(
        default=False,
        description="Whether this source was discovered by AI",
    )
    added_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this source was added",
    )
    notes: Optional[str] = Field(default=None, description="Optional notes about the source")

    def should_fetch(self) -> bool:
        """Check if enough time has passed since last fetch."""
        if not self.enabled:
            return False
        if self.last_fetched is None:
            return True
        hours_since = (datetime.utcnow() - self.last_fetched).total_seconds() / 3600
        return hours_since >= self.fetch_interval_hours
