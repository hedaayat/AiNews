# AiNews

AI News Aggregator - Collects AI news from various sources and generates daily summaries using Claude.

## Features

- **RSS/Atom Feed Support**: Parse news from RSS and Atom feeds
- **Web Scraping**: Extract articles from websites without feeds
- **AI Summarization**: Generate daily summaries using Claude API
- **Email Delivery**: Receive summaries in your inbox
- **AI Source Discovery**: Let Claude suggest new sources
- **Deduplication**: Automatic removal of duplicate articles

## Quick Start

1. **Install with uv (recommended)**
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

2. **Configure**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run**
   ```bash
   # Full pipeline: fetch, summarize, send
   uv run ainews run

   # Or step by step:
   uv run ainews fetch
   uv run ainews summarize
   uv run ainews send
   ```

## CLI Commands

```bash
ainews --help                   # Show all commands

# Sources
ainews source list              # List configured sources
ainews source add URL --name "Name"  # Add a source
ainews source discover          # AI-suggested sources

# Operations
ainews fetch                    # Fetch from all sources
ainews summarize                # Generate summary
ainews send                     # Email summary
ainews run                      # Full pipeline

# Info
ainews status                   # System status
ainews articles                 # List today's articles
```

## Configuration

Set these environment variables (or in `.env`):

| Variable | Required | Description |
|----------|----------|-------------|
| `AINEWS_ANTHROPIC_API_KEY` | Yes | Claude API key |
| `AINEWS_SMTP_HOST` | For email | SMTP server |
| `AINEWS_SMTP_PORT` | For email | SMTP port (default: 587) |
| `AINEWS_SMTP_USERNAME` | For email | SMTP username |
| `AINEWS_SMTP_PASSWORD` | For email | SMTP password |
| `AINEWS_EMAIL_FROM` | For email | Sender address |
| `AINEWS_EMAIL_TO` | For email | Recipients (JSON array) |

## Default Sources

The app comes pre-configured with these AI news sources:

- OpenAI Blog
- Anthropic News
- Google AI Blog
- MIT Technology Review - AI
- The Verge - AI
- Ars Technica
- VentureBeat - AI
- Hugging Face Blog

## Scheduling

### Linux/macOS (cron)
```bash
# Run daily at 8 AM
0 8 * * * cd /path/to/ainews && python -m ainews run
```

### Windows (Task Scheduler)
Create a task to run `python -m ainews run` daily.

## License

MIT
