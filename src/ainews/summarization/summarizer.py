"""AI-powered news summarization."""

import json
from datetime import date, datetime

from ainews.config import Settings
from ainews.models.article import Article
from ainews.models.summary import DailySummary, NotableStory
from ainews.storage.json_store import DatePartitionedStore
from ainews.summarization.client import ClaudeClient

SYSTEM_PROMPT = """You are an AI news summarizer. Your task is to create a comprehensive yet concise daily summary of AI news articles.

Guidelines:
1. Focus on the most significant developments and trends
2. Group related stories together by theme
3. Highlight key players, companies, and technologies mentioned
4. Note any important implications or potential impacts
5. Keep the tone informative and professional
6. Include specific details and numbers when relevant

Output Format:
Respond with a JSON object containing:
{
  "summary": "A 2-4 paragraph summary covering the day's key AI developments",
  "key_topics": ["topic1", "topic2", ...],  // 3-5 main topics covered
  "notable_stories": [
    {
      "title": "Story title",
      "source": "Source name",
      "brief": "One sentence description",
      "url": "Article URL"
    }
  ]  // 3-5 most notable stories
}"""


class Summarizer:
    """Generates AI-powered news summaries."""

    def __init__(self, settings: Settings):
        """Initialize the summarizer.

        Args:
            settings: Application settings.
        """
        self.settings = settings
        self.client = ClaudeClient(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
        )
        self.article_store = DatePartitionedStore(settings.articles_dir, Article)
        self.summary_store = DatePartitionedStore(settings.summaries_dir, DailySummary)

    def generate_summary(
        self,
        target_date: date | None = None,
        articles: list[Article] | None = None,
    ) -> DailySummary | None:
        """Generate a daily summary.

        Args:
            target_date: Date to summarize. Defaults to today.
            articles: Optional list of articles. If None, loads from store.

        Returns:
            Generated summary, or None if no articles.
        """
        target_date = target_date or date.today()

        # Load articles if not provided
        if articles is None:
            articles = self.article_store.load(target_date)

        if not articles:
            print(f"No articles found for {target_date}")
            return None

        # Limit articles
        if len(articles) > self.settings.max_articles_per_summary:
            # Sort by publication date and take most recent
            articles = sorted(
                articles,
                key=lambda a: a.published_at or a.fetched_at,
                reverse=True,
            )[: self.settings.max_articles_per_summary]

        # Build prompt
        prompt = self._build_prompt(articles)

        # Generate summary
        response_text, tokens_used = self.client.generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
        )

        # Parse response
        summary = self._parse_response(response_text, articles, target_date, tokens_used)

        # Save summary
        self.summary_store.save(target_date, [summary])

        return summary

    def _build_prompt(self, articles: list[Article]) -> str:
        """Build the prompt from articles."""
        prompt_parts = [
            f"Please summarize the following {len(articles)} AI news articles from today:\n\n"
        ]

        for i, article in enumerate(articles, 1):
            prompt_parts.append(f"--- Article {i} ---")
            prompt_parts.append(f"Title: {article.title}")
            prompt_parts.append(f"Source: {article.source_id}")
            prompt_parts.append(f"URL: {article.url}")
            if article.published_at:
                prompt_parts.append(f"Published: {article.published_at.isoformat()}")
            if article.content:
                # Truncate very long content
                content = article.content[:2000]
                if len(article.content) > 2000:
                    content += "..."
                prompt_parts.append(f"Content: {content}")
            prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _parse_response(
        self,
        response_text: str,
        articles: list[Article],
        target_date: date,
        tokens_used: int,
    ) -> DailySummary:
        """Parse Claude's response into a DailySummary."""
        try:
            # Strip markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove lines that are just ``` or ```json
                lines = [line for line in lines if not line.strip().startswith("```")]
                text = "\n".join(lines).strip()

            # Try to parse as JSON
            data = json.loads(text)

            notable_stories = []
            for story in data.get("notable_stories", []):
                notable_stories.append(
                    NotableStory(
                        title=story.get("title", ""),
                        source=story.get("source", ""),
                        brief=story.get("brief", ""),
                        url=story.get("url", ""),
                    )
                )

            return DailySummary(
                date=target_date,
                generated_at=datetime.utcnow(),
                article_count=len(articles),
                article_ids=[a.id for a in articles],
                summary_text=data.get("summary", response_text),
                key_topics=data.get("key_topics", []),
                notable_stories=notable_stories,
                model_used=self.settings.claude_model,
                tokens_used=tokens_used,
            )

        except json.JSONDecodeError:
            # If not valid JSON, use raw text as summary
            return DailySummary(
                date=target_date,
                generated_at=datetime.utcnow(),
                article_count=len(articles),
                article_ids=[a.id for a in articles],
                summary_text=response_text,
                key_topics=[],
                notable_stories=[],
                model_used=self.settings.claude_model,
                tokens_used=tokens_used,
            )

    def get_summary(self, target_date: date | None = None) -> DailySummary | None:
        """Get an existing summary for a date.

        Args:
            target_date: Date to get summary for. Defaults to today.

        Returns:
            Existing summary, or None if not found.
        """
        target_date = target_date or date.today()
        summaries = self.summary_store.load(target_date)
        return summaries[0] if summaries else None
