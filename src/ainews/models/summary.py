"""Summary data model."""

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field


class NotableStory(BaseModel):
    """A notable story highlighted in the summary."""

    title: str = Field(description="Story title")
    source: str = Field(description="Source name")
    brief: str = Field(description="Brief description")
    url: str = Field(description="Article URL")


class DailySummary(BaseModel):
    """A daily summary of AI news."""

    date: dt.date = Field(description="Date of the summary")
    generated_at: dt.datetime = Field(
        default_factory=dt.datetime.utcnow,
        description="When this summary was generated",
    )
    article_count: int = Field(description="Number of articles summarized")
    article_ids: list[str] = Field(
        default_factory=list,
        description="IDs of articles included in the summary",
    )
    summary_text: str = Field(description="The generated summary text")
    key_topics: list[str] = Field(
        default_factory=list,
        description="Key topics covered in the summary",
    )
    notable_stories: list[NotableStory] = Field(
        default_factory=list,
        description="Notable stories with brief descriptions",
    )
    model_used: str = Field(description="Claude model used for generation")
    tokens_used: Optional[int] = Field(
        default=None,
        description="Total tokens used for generation",
    )
    delivered: bool = Field(default=False, description="Whether the summary has been delivered")
    delivered_at: Optional[dt.datetime] = Field(
        default=None,
        description="When the summary was delivered",
    )

    def mark_delivered(self) -> None:
        """Mark this summary as delivered."""
        self.delivered = True
        self.delivered_at = dt.datetime.utcnow()
