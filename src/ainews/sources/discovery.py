"""AI-assisted source discovery."""

import json

from ainews.summarization.client import ClaudeClient

DISCOVERY_SYSTEM_PROMPT = """You are an expert at finding high-quality news sources for AI and technology topics.

When suggesting sources, prioritize:
1. Official company blogs (OpenAI, Anthropic, Google AI, Meta AI, etc.)
2. Reputable tech news sites with AI coverage
3. Academic/research publication feeds
4. Industry analysis sites
5. Sources with RSS/Atom feeds (preferred over scraping)

For each source, provide accurate, verified URLs. Only suggest sources you are confident exist."""


class SourceDiscovery:
    """AI-assisted discovery of news sources."""

    def __init__(self, client: ClaudeClient):
        """Initialize source discovery.

        Args:
            client: Claude API client.
        """
        self.client = client

    async def suggest_sources(
        self,
        topic: str = "artificial intelligence",
        count: int = 5,
    ) -> list[dict]:
        """Suggest news sources for a topic.

        Args:
            topic: Topic to find sources for.
            count: Number of sources to suggest.

        Returns:
            List of suggested source dictionaries.
        """
        prompt = f"""Suggest {count} high-quality news sources for the topic: "{topic}"

For each source, provide a JSON array with objects containing:
- name: Display name of the source
- url: The RSS/Atom feed URL if available, otherwise the main page URL
- type: "rss" if it's an RSS/Atom feed, "web" if it requires scraping
- description: Brief description of what the source covers

Respond with only the JSON array, no other text.

Example format:
[
  {{
    "name": "Example AI Blog",
    "url": "https://example.com/ai/feed.xml",
    "type": "rss",
    "description": "Covers AI research and industry news"
  }}
]"""

        response_text, _ = self.client.generate(
            prompt=prompt,
            system=DISCOVERY_SYSTEM_PROMPT,
            max_tokens=2000,
        )

        # Parse response
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove markdown code blocks
                lines = response_text.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block or not line.startswith("```"):
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            suggestions = json.loads(response_text)

            if isinstance(suggestions, list):
                return suggestions

            return []

        except json.JSONDecodeError:
            print(f"Failed to parse discovery response: {response_text[:200]}")
            return []

    async def validate_source(self, url: str) -> dict:
        """Validate a potential source URL.

        Args:
            url: URL to validate.

        Returns:
            Validation result with source info.
        """
        from ainews.sources.validator import validate_source

        result = await validate_source(url)

        return {
            "valid": result.valid,
            "source_type": result.source_type.value if result.source_type else None,
            "title": result.title,
            "error": result.error,
        }
