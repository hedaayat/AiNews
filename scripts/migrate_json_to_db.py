#!/usr/bin/env python
"""
Migrate data from JSON files to PostgreSQL database.

This script:
1. Reads sources from data/sources.json
2. Reads articles from data/articles/*.json
3. Inserts them into the PostgreSQL database via Supabase

Usage:
    python scripts/migrate_json_to_db.py
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ainews.config import get_settings
from ainews.db.models import Source, Article, Summary, NotableStory


async def load_json_file(file_path: Path) -> dict:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_iso_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string to Python datetime object."""
    if not dt_string:
        return None
    try:
        return datetime.fromisoformat(dt_string)
    except (ValueError, TypeError):
        return None


async def migrate_sources(session: AsyncSession, data_dir: Path) -> int:
    """Migrate sources from data/sources.json to database."""
    sources_file = data_dir / "sources.json"

    if not sources_file.exists():
        print(f"❌ Sources file not found: {sources_file}")
        return 0

    data = await load_json_file(sources_file)
    items = data.get("items", [])

    print(f"\n📚 Migrating {len(items)} sources...")

    migrated = 0
    for item in items:
        try:
            # Check if source already exists
            stmt = select(Source).where(Source.id == item["id"])
            existing = await session.execute(stmt)
            if existing.scalar_one_or_none():
                print(f"  ⏭️  Source '{item['name']}' already exists, skipping")
                continue

            # Create source record
            source = Source(
                id=item["id"],
                name=item["name"],
                url=item["url"],
                source_type=item.get("source_type", "rss"),
                enabled=item.get("enabled", True),
                tags=item.get("tags", []),
                last_fetched=parse_iso_datetime(item.get("last_fetched")),
                fetch_interval_hours=item.get("fetch_interval_hours", 24),
                added_at=parse_iso_datetime(item.get("added_at")),
            )
            session.add(source)
            await session.flush()  # Flush to catch errors early
            migrated += 1
            print(f"  ✅ Added source: {item['name']}")
        except Exception as e:
            await session.rollback()  # Rollback failed insert
            print(f"  ❌ Error adding source {item.get('id')}: {str(e)[:100]}")

    await session.commit()
    print(f"✅ Migrated {migrated} sources")
    return migrated


async def migrate_articles(session: AsyncSession, data_dir: Path) -> int:
    """Migrate articles from data/articles/*.json to database."""
    articles_dir = data_dir / "articles"

    if not articles_dir.exists():
        print(f"❌ Articles directory not found: {articles_dir}")
        return 0

    article_files = sorted(articles_dir.glob("*.json"))
    print(f"\n📰 Found {len(article_files)} article files")

    total_migrated = 0

    for article_file in article_files:
        print(f"\n  Processing {article_file.name}...")

        try:
            data = await load_json_file(article_file)
            items = data.get("items", [])

            migrated = 0
            for item in items:
                try:
                    # Check if article already exists by URL
                    stmt = select(Article).where(Article.url == item["url"])
                    existing = await session.execute(stmt)
                    if existing.scalar_one_or_none():
                        continue  # Article already exists

                    # Create article record
                    article = Article(
                        id=item["id"],
                        title=item["title"],
                        url=item["url"],
                        source_id=item["source_id"],
                        content=item.get("content", ""),
                        content_hash=item.get("content_hash", ""),
                        published_at=parse_iso_datetime(item.get("published_at")),
                        fetched_at=parse_iso_datetime(item.get("fetched_at")),
                        word_count=item.get("word_count", 0),
                        tags=item.get("tags", []),
                    )
                    session.add(article)
                    migrated += 1
                except Exception as e:
                    await session.rollback()  # Rollback failed insert
                    print(f"    ❌ Error adding article {item.get('id')}: {str(e)[:80]}")

            if migrated > 0:
                await session.flush()  # Flush to catch constraint violations
                print(f"    ✅ Processed {migrated} new articles from {article_file.name}")
                total_migrated += migrated
        except Exception as e:
            print(f"  ❌ Error processing {article_file.name}: {e}")

    await session.commit()
    print(f"\n✅ Migrated {total_migrated} articles total")
    return total_migrated


async def main():
    """Run the migration."""
    settings = get_settings()
    data_dir = settings.data_dir

    print("=" * 60)
    print("🚀 JSON to PostgreSQL Migration")
    print("=" * 60)
    print(f"📁 Data directory: {data_dir}")

    # Extract host from database URL safely
    try:
        db_host = settings.database_url.split('@')[1].split('/')[0] if '@' in settings.database_url else 'unknown'
    except:
        db_host = 'unknown'
    print(f"🗄️  Database: {db_host}")

    # Create async engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
    )

    # Create session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True,
    )

    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("\n✅ Database connection successful")

        # Run migrations
        async with AsyncSessionLocal() as session:
            sources_migrated = await migrate_sources(session, data_dir)
            articles_migrated = await migrate_articles(session, data_dir)

        print("\n" + "=" * 60)
        print("✅ Migration completed!")
        print(f"   • Sources: {sources_migrated}")
        print(f"   • Articles: {articles_migrated}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
