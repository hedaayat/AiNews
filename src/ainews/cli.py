"""Command-line interface for AiNews."""

import asyncio
from datetime import date, datetime

import typer
from rich.console import Console
from rich.table import Table

from ainews.config import get_settings
from ainews.models.source import SourceType

app = typer.Typer(
    name="ainews",
    help="AI News Aggregator - Collects AI news and generates daily summaries",
    no_args_is_help=True,
)
source_app = typer.Typer(help="Manage news sources")
app.add_typer(source_app, name="source")

console = Console()


# ============================================================================
# Source Commands
# ============================================================================


@source_app.command("list")
def source_list(
    all_sources: bool = typer.Option(False, "--all", "-a", help="Include disabled sources"),
):
    """List configured news sources."""
    settings = get_settings()
    settings.ensure_directories()

    from ainews.sources.manager import SourceManager

    manager = SourceManager(settings.sources_file)
    sources = manager.list_sources(enabled_only=not all_sources)

    if not sources:
        console.print("[yellow]No sources configured[/yellow]")
        return

    table = Table(title="News Sources")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Enabled")
    table.add_column("Last Fetched")

    for source in sources:
        last_fetched = source.last_fetched.strftime("%Y-%m-%d %H:%M") if source.last_fetched else "Never"
        table.add_row(
            source.id,
            source.name,
            source.source_type.value,
            "✓" if source.enabled else "✗",
            last_fetched,
        )

    console.print(table)


@source_app.command("add")
def source_add(
    url: str = typer.Argument(..., help="URL of the feed or page"),
    name: str = typer.Option(..., "--name", "-n", help="Display name for the source"),
    source_type: str = typer.Option("rss", "--type", "-t", help="Source type: rss, atom, web"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
):
    """Add a new news source."""
    settings = get_settings()
    settings.ensure_directories()

    from ainews.sources.manager import SourceManager

    manager = SourceManager(settings.sources_file)

    # Parse source type
    try:
        st = SourceType(source_type.lower())
    except ValueError:
        console.print(f"[red]Invalid source type: {source_type}[/red]")
        raise typer.Exit(1)

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    source = manager.add_source(url=url, name=name, source_type=st, tags=tag_list)
    console.print(f"[green]Added source:[/green] {source.id} ({source.name})")


@source_app.command("remove")
def source_remove(
    source_id: str = typer.Argument(..., help="ID of the source to remove"),
):
    """Remove a news source."""
    settings = get_settings()

    from ainews.sources.manager import SourceManager

    manager = SourceManager(settings.sources_file)

    if manager.remove_source(source_id):
        console.print(f"[green]Removed source:[/green] {source_id}")
    else:
        console.print(f"[red]Source not found:[/red] {source_id}")
        raise typer.Exit(1)


@source_app.command("enable")
def source_enable(
    source_id: str = typer.Argument(..., help="ID of the source to enable"),
):
    """Enable a news source."""
    settings = get_settings()

    from ainews.sources.manager import SourceManager

    manager = SourceManager(settings.sources_file)

    if manager.enable_source(source_id):
        console.print(f"[green]Enabled source:[/green] {source_id}")
    else:
        console.print(f"[red]Source not found:[/red] {source_id}")
        raise typer.Exit(1)


@source_app.command("disable")
def source_disable(
    source_id: str = typer.Argument(..., help="ID of the source to disable"),
):
    """Disable a news source."""
    settings = get_settings()

    from ainews.sources.manager import SourceManager

    manager = SourceManager(settings.sources_file)

    if manager.disable_source(source_id):
        console.print(f"[yellow]Disabled source:[/yellow] {source_id}")
    else:
        console.print(f"[red]Source not found:[/red] {source_id}")
        raise typer.Exit(1)


@source_app.command("discover")
def source_discover(
    topic: str = typer.Option("artificial intelligence", "--topic", "-t", help="Topic to search for"),
):
    """Use AI to discover new news sources."""
    settings = get_settings()
    settings.ensure_directories()

    from ainews.sources.discovery import SourceDiscovery
    from ainews.summarization.client import ClaudeClient

    client = ClaudeClient(api_key=settings.anthropic_api_key, model=settings.claude_model)
    discovery = SourceDiscovery(client)

    console.print(f"[cyan]Discovering sources for:[/cyan] {topic}")

    suggestions = asyncio.run(discovery.suggest_sources(topic))

    if not suggestions:
        console.print("[yellow]No sources discovered[/yellow]")
        return

    table = Table(title="Suggested Sources")
    table.add_column("Name")
    table.add_column("URL")
    table.add_column("Type")
    table.add_column("Description")

    for suggestion in suggestions:
        table.add_row(
            suggestion.get("name", ""),
            suggestion.get("url", ""),
            suggestion.get("type", ""),
            suggestion.get("description", "")[:50] + "...",
        )

    console.print(table)
    console.print("\n[dim]Use 'ainews source add' to add these sources[/dim]")


# ============================================================================
# Fetch Commands
# ============================================================================


@app.command("fetch")
def fetch(
    source_id: str = typer.Option(None, "--source", "-s", help="Fetch specific source only"),
    force: bool = typer.Option(False, "--force", "-f", help="Force fetch regardless of interval"),
):
    """Fetch articles from news sources."""
    settings = get_settings()
    settings.ensure_directories()

    from ainews.fetchers.orchestrator import FetchOrchestrator

    orchestrator = FetchOrchestrator(settings)

    console.print("[cyan]Fetching articles...[/cyan]")

    if source_id:
        articles = asyncio.run(orchestrator.fetch_single(source_id))
    else:
        articles = asyncio.run(orchestrator.fetch_all(force=force))

    console.print(f"[green]Fetched {len(articles)} new articles[/green]")


# ============================================================================
# Summarize Commands
# ============================================================================


@app.command("summarize")
def summarize(
    target_date: str = typer.Option(None, "--date", "-d", help="Date to summarize (YYYY-MM-DD)"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview without saving"),
):
    """Generate a summary of today's articles."""
    settings = get_settings()
    settings.ensure_directories()

    from ainews.summarization.summarizer import Summarizer

    summarizer = Summarizer(settings)

    # Parse date
    if target_date:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            console.print(f"[red]Invalid date format:[/red] {target_date}")
            raise typer.Exit(1)
    else:
        dt = date.today()

    console.print(f"[cyan]Generating summary for {dt}...[/cyan]")

    summary = summarizer.generate_summary(target_date=dt)

    if not summary:
        console.print("[yellow]No articles to summarize[/yellow]")
        return

    console.print("\n[bold]Summary:[/bold]")
    console.print(summary.summary_text)

    if summary.key_topics:
        console.print(f"\n[bold]Key Topics:[/bold] {', '.join(summary.key_topics)}")

    console.print(f"\n[dim]Based on {summary.article_count} articles, {summary.tokens_used} tokens used[/dim]")


# ============================================================================
# Send Commands
# ============================================================================


@app.command("send")
def send(
    target_date: str = typer.Option(None, "--date", "-d", help="Date to send (YYYY-MM-DD)"),
    to: str = typer.Option(None, "--to", "-t", help="Override recipient email"),
):
    """Send the daily summary via email."""
    settings = get_settings()
    settings.ensure_directories()

    from ainews.delivery.email import EmailDelivery
    from ainews.summarization.summarizer import Summarizer

    summarizer = Summarizer(settings)
    delivery = EmailDelivery(settings)

    # Parse date
    if target_date:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            console.print(f"[red]Invalid date format:[/red] {target_date}")
            raise typer.Exit(1)
    else:
        dt = date.today()

    # Get summary
    summary = summarizer.get_summary(dt)

    if not summary:
        console.print(f"[yellow]No summary found for {dt}. Run 'ainews summarize' first.[/yellow]")
        raise typer.Exit(1)

    # Override recipients if specified
    recipients = [to] if to else None

    console.print(f"[cyan]Sending summary for {dt}...[/cyan]")

    if delivery.send_summary(summary, recipients):
        console.print("[green]Summary sent successfully![/green]")
    else:
        console.print("[red]Failed to send summary[/red]")
        raise typer.Exit(1)


# ============================================================================
# Run Command (Full Pipeline)
# ============================================================================


@app.command("run")
def run(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would happen without executing"),
):
    """Run the full pipeline: fetch, summarize, and send."""
    settings = get_settings()
    settings.ensure_directories()

    if dry_run:
        console.print("[yellow]Dry run mode - no changes will be made[/yellow]")
        console.print("\nWould execute:")
        console.print("  1. Fetch articles from all enabled sources")
        console.print("  2. Generate summary using Claude")
        console.print("  3. Send summary via email")
        return

    from ainews.delivery.email import EmailDelivery
    from ainews.fetchers.orchestrator import FetchOrchestrator
    from ainews.summarization.summarizer import Summarizer

    # Step 1: Fetch
    console.print("[cyan]Step 1/3: Fetching articles...[/cyan]")
    orchestrator = FetchOrchestrator(settings)
    articles = asyncio.run(orchestrator.fetch_all())
    console.print(f"  Fetched {len(articles)} new articles")

    # Step 2: Summarize
    console.print("[cyan]Step 2/3: Generating summary...[/cyan]")
    summarizer = Summarizer(settings)
    summary = summarizer.generate_summary()

    if not summary:
        console.print("[yellow]  No articles to summarize[/yellow]")
        return

    console.print(f"  Generated summary from {summary.article_count} articles")

    # Step 3: Send
    console.print("[cyan]Step 3/3: Sending email...[/cyan]")
    delivery = EmailDelivery(settings)

    if delivery.send_summary(summary):
        console.print("[green]  Summary sent successfully![/green]")
    else:
        console.print("[red]  Failed to send summary[/red]")

    console.print("\n[green]Pipeline complete![/green]")


# ============================================================================
# Status Command
# ============================================================================


@app.command("status")
def status():
    """Show system status and statistics."""
    settings = get_settings()

    console.print("[bold]AiNews Status[/bold]\n")

    # Check directories
    console.print("[cyan]Directories:[/cyan]")
    console.print(f"  Data: {settings.data_dir} ({'exists' if settings.data_dir.exists() else 'missing'})")
    console.print(f"  Articles: {settings.articles_dir} ({'exists' if settings.articles_dir.exists() else 'missing'})")
    console.print(f"  Summaries: {settings.summaries_dir} ({'exists' if settings.summaries_dir.exists() else 'missing'})")

    # Check sources
    console.print("\n[cyan]Sources:[/cyan]")
    if settings.sources_file.exists():
        from ainews.sources.manager import SourceManager

        manager = SourceManager(settings.sources_file)
        all_sources = manager.list_sources(enabled_only=False)
        enabled = [s for s in all_sources if s.enabled]
        console.print(f"  Total: {len(all_sources)}")
        console.print(f"  Enabled: {len(enabled)}")
    else:
        console.print("  [yellow]No sources configured[/yellow]")

    # Check API key
    console.print("\n[cyan]Configuration:[/cyan]")
    console.print(f"  Anthropic API: {'configured' if settings.anthropic_api_key else 'missing'}")
    console.print(f"  SMTP: {'configured' if settings.smtp_username else 'not configured'}")
    console.print(f"  Claude Model: {settings.claude_model}")


# ============================================================================
# Articles Command
# ============================================================================


@app.command("articles")
def articles(
    target_date: str = typer.Option(None, "--date", "-d", help="Date to show (YYYY-MM-DD)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum articles to show"),
):
    """List fetched articles."""
    settings = get_settings()

    from ainews.models.article import Article
    from ainews.storage.json_store import DatePartitionedStore

    store = DatePartitionedStore(settings.articles_dir, Article)

    # Parse date
    if target_date:
        try:
            dt = date.fromisoformat(target_date)
        except ValueError:
            console.print(f"[red]Invalid date format:[/red] {target_date}")
            raise typer.Exit(1)
    else:
        dt = date.today()

    articles_list = store.load(dt)

    if not articles_list:
        console.print(f"[yellow]No articles found for {dt}[/yellow]")
        return

    console.print(f"[bold]Articles for {dt}[/bold] ({len(articles_list)} total)\n")

    for article in articles_list[:limit]:
        console.print(f"[cyan]{article.title}[/cyan]")
        console.print(f"  Source: {article.source_id}")
        console.print(f"  URL: {article.url}")
        if article.published_at:
            console.print(f"  Published: {article.published_at}")
        console.print(f"  Words: {article.word_count}")
        console.print()


if __name__ == "__main__":
    app()
