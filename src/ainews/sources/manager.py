"""Source management operations."""

import re
from datetime import datetime
from pathlib import Path

from ainews.models.source import Source, SourceType
from ainews.storage.json_store import JsonStore


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


class SourceManager:
    """Manages news sources."""

    def __init__(self, sources_file: Path):
        self.store = JsonStore(sources_file, Source)

    def list_sources(self, enabled_only: bool = True) -> list[Source]:
        """List all sources, optionally filtering by enabled status."""
        sources = self.store.load()
        if enabled_only:
            return [s for s in sources if s.enabled]
        return sources

    def get_source(self, source_id: str) -> Source | None:
        """Get a source by ID."""
        return self.store.get_by_id(source_id)

    def add_source(
        self,
        url: str,
        name: str,
        source_type: SourceType = SourceType.RSS,
        tags: list[str] | None = None,
        scrape_selector: str | None = None,
        discovered_by_ai: bool = False,
    ) -> Source:
        """Add a new source."""
        source_id = slugify(name)

        # Check for duplicate ID
        if self.store.exists(source_id):
            # Append a number to make it unique
            counter = 2
            while self.store.exists(f"{source_id}-{counter}"):
                counter += 1
            source_id = f"{source_id}-{counter}"

        source = Source(
            id=source_id,
            name=name,
            url=url,
            source_type=source_type,
            tags=tags or [],
            scrape_selector=scrape_selector,
            discovered_by_ai=discovered_by_ai,
            added_at=datetime.utcnow(),
        )

        self.store.append(source)
        return source

    def update_source(self, source_id: str, **updates: dict) -> Source | None:
        """Update a source with new values."""
        source = self.get_source(source_id)
        if not source:
            return None

        # Create updated source
        source_data = source.model_dump()
        source_data.update(updates)
        updated_source = Source.model_validate(source_data)

        self.store.update(source_id, updated_source)
        return updated_source

    def remove_source(self, source_id: str) -> bool:
        """Remove a source."""
        return self.store.delete(source_id)

    def enable_source(self, source_id: str) -> bool:
        """Enable a source."""
        result = self.update_source(source_id, enabled=True)
        return result is not None

    def disable_source(self, source_id: str) -> bool:
        """Disable a source."""
        result = self.update_source(source_id, enabled=False)
        return result is not None

    def mark_fetched(self, source_id: str) -> bool:
        """Mark a source as fetched."""
        result = self.update_source(source_id, last_fetched=datetime.utcnow())
        return result is not None

    def get_sources_to_fetch(self) -> list[Source]:
        """Get sources that should be fetched based on their interval."""
        sources = self.list_sources(enabled_only=True)
        return [s for s in sources if s.should_fetch()]
