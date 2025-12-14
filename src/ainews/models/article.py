"""Article data model."""

import hashlib
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, computed_field


class Article(BaseModel):
    """A fetched news article."""

    id: str = Field(description="Unique identifier (hash of URL)")
    title: str = Field(description="Article title")
    url: HttpUrl = Field(description="Article URL")
    source_id: str = Field(description="ID of the source this article came from")
    published_at: Optional[datetime] = Field(
        default=None,
        description="Publication date from the source",
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this article was fetched",
    )
    content: str = Field(default="", description="Extracted article content")
    summary: Optional[str] = Field(
        default=None,
        description="Per-article summary if generated",
    )
    content_hash: str = Field(default="", description="Hash of content for deduplication")
    tags: list[str] = Field(default_factory=list, description="Tags/categories")

    @computed_field
    @property
    def word_count(self) -> int:
        """Count words in the article content."""
        return len(self.content.split())

    @classmethod
    def generate_id(cls, url: str) -> str:
        """Generate a unique ID from URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        """Generate a hash of the content for deduplication."""
        normalized = " ".join(content.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def update_content(self, content: str) -> None:
        """Update content and recalculate hash."""
        self.content = content
        self.content_hash = self.generate_content_hash(content)
