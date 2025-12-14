# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AiNews is a Python application that aggregates AI-related news from RSS feeds and web scraping, generates daily summaries using Claude API, and delivers them via email.

## Commands

```bash
# Install dependencies (uv recommended)
uv sync

# Or with pip
pip install -e .

# Run CLI
uv run ainews --help

# Source management
ainews source list              # List all sources
ainews source add <url> --name "Name" --type rss
ainews source remove <id>
ainews source discover          # AI-assisted source discovery

# Operations
ainews fetch                    # Fetch articles from all sources
ainews fetch --force            # Force fetch regardless of interval
ainews summarize                # Generate today's summary
ainews send                     # Email today's summary
ainews run                      # Full pipeline: fetch + summarize + send

# Status
ainews status                   # Show system status
ainews articles --date 2024-01-15  # List articles for a date
```

## Architecture

```
src/ainews/
├── cli.py              # Typer CLI interface
├── config.py           # Settings via pydantic-settings (env vars)
├── models/             # Pydantic data models (Source, Article, DailySummary)
├── sources/            # Source management and AI discovery
├── fetchers/           # RSS and web scraping fetchers
├── processing/         # Content extraction and deduplication
├── summarization/      # Claude API integration
├── delivery/           # Email sender
└── storage/            # JSON file persistence with locking
```

## Key Files

- `src/ainews/config.py` - All settings from `AINEWS_*` environment variables
- `src/ainews/fetchers/orchestrator.py` - Coordinates parallel fetching
- `src/ainews/summarization/summarizer.py` - Claude-powered summary generation
- `data/sources.json` - Configured news sources (seed file included)

## Data Storage

- `data/sources.json` - News source configurations (20 pre-configured feeds)
- `data/source_candidates.json` - Candidate sources for adding
- `data/articles/YYYY-MM-DD.json` - Articles partitioned by date
- `data/summaries/YYYY-MM-DD.json` - Generated summaries by date

## Source Categories

The app includes 20 curated sources across categories:
- **Company blogs**: OpenAI, Google AI, DeepMind, Microsoft Research, NVIDIA, Hugging Face
- **News sites**: MIT Tech Review, The Verge, Ars Technica, VentureBeat
- **Academic**: BAIR, MIT News, arXiv (cs.AI, cs.LG)
- **Newsletters**: The Gradient, AI Alignment Forum, Sebastian Raschka, Andrej Karpathy, Distill

## Configuration

Copy `.env.example` to `.env` and set:
- `AINEWS_ANTHROPIC_API_KEY` - Required for summarization
- `AINEWS_SMTP_*` - Required for email delivery
