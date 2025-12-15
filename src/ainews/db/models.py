"""SQLAlchemy ORM models for the web application."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    TEXT,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.orm import relationship

from ainews.db.base import Base


class Source(Base):
    """News source model."""

    __tablename__ = "sources"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # RSS, ATOM, WEB
    enabled = Column(Integer, default=1)  # 1 = enabled, 0 = disabled
    tags = Column(ARRAY(String), nullable=True)
    last_fetched = Column(TIMESTAMP(timezone=True), nullable=True)
    fetch_interval_hours = Column(Integer, default=24)
    added_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    articles = relationship("Article", back_populates="source")

    def __repr__(self) -> str:
        return f"<Source {self.name}>"


class Article(Base):
    """Article model."""

    __tablename__ = "articles"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    source_id = Column(String, ForeignKey("sources.id"), nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)
    published_at = Column(TIMESTAMP(timezone=True), nullable=True)
    fetched_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    word_count = Column(Integer, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    source = relationship("Source", back_populates="articles")

    __table_args__ = (
        Index("idx_articles_published", "published_at", postgresql_using="btree"),
        Index("idx_articles_source", "source_id", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return f"<Article {self.title[:50]}>"


class Summary(Base):
    """Daily summary model."""

    __tablename__ = "summaries"

    date = Column(String, primary_key=True)  # YYYY-MM-DD format
    summary_text = Column(Text, nullable=False)
    key_topics = Column(ARRAY(String), nullable=True)
    article_count = Column(Integer, nullable=False)
    article_ids = Column(ARRAY(String), nullable=True)
    generated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Summary {self.date}>"


class NotableStory(Base):
    """Notable story in daily summary."""

    __tablename__ = "notable_stories"

    id = Column(Integer, primary_key=True)
    summary_date = Column(String, ForeignKey("summaries.date"), nullable=False)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    brief = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    position = Column(Integer, nullable=False)

    __table_args__ = (Index("idx_notable_stories_date", "summary_date"),)

    def __repr__(self) -> str:
        return f"<NotableStory {self.title[:30]}>"
