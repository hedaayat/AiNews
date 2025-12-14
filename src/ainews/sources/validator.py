"""Source URL validation."""

from typing import NamedTuple

import httpx

from ainews.models.source import SourceType


class ValidationResult(NamedTuple):
    """Result of source validation."""

    valid: bool
    source_type: SourceType | None
    title: str | None
    error: str | None


async def validate_source(
    url: str,
    timeout: int = 10,
    user_agent: str = "AiNews/1.0",
) -> ValidationResult:
    """Validate a source URL and detect its type."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                url,
                headers={"User-Agent": user_agent},
                follow_redirects=True,
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            content = response.text[:5000]  # Only check first 5KB

            # Check for RSS/Atom feed indicators
            source_type, title = _detect_feed_type(content, content_type)

            if source_type:
                return ValidationResult(
                    valid=True,
                    source_type=source_type,
                    title=title,
                    error=None,
                )

            # If not a feed, it's a web page
            return ValidationResult(
                valid=True,
                source_type=SourceType.WEB,
                title=_extract_html_title(content),
                error=None,
            )

    except httpx.TimeoutException:
        return ValidationResult(
            valid=False,
            source_type=None,
            title=None,
            error="Request timed out",
        )
    except httpx.HTTPStatusError as e:
        return ValidationResult(
            valid=False,
            source_type=None,
            title=None,
            error=f"HTTP error: {e.response.status_code}",
        )
    except Exception as e:
        return ValidationResult(
            valid=False,
            source_type=None,
            title=None,
            error=str(e),
        )


def _detect_feed_type(content: str, content_type: str) -> tuple[SourceType | None, str | None]:
    """Detect if content is RSS or Atom feed."""
    content_lower = content.lower()

    # Check content type header
    if "application/rss" in content_type or "application/atom" in content_type:
        if "atom" in content_type:
            return SourceType.ATOM, _extract_feed_title(content)
        return SourceType.RSS, _extract_feed_title(content)

    # Check XML content
    if "application/xml" in content_type or "text/xml" in content_type:
        if "<feed" in content_lower and "xmlns" in content_lower:
            return SourceType.ATOM, _extract_feed_title(content)
        if "<rss" in content_lower or "<channel>" in content_lower:
            return SourceType.RSS, _extract_feed_title(content)

    # Check content itself
    if "<feed" in content_lower and ("atom" in content_lower or "xmlns" in content_lower):
        return SourceType.ATOM, _extract_feed_title(content)
    if "<rss" in content_lower or ("<channel>" in content_lower and "<item>" in content_lower):
        return SourceType.RSS, _extract_feed_title(content)

    return None, None


def _extract_feed_title(content: str) -> str | None:
    """Extract title from RSS/Atom feed."""
    import re

    # Try to find <title> tag
    match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_html_title(content: str) -> str | None:
    """Extract title from HTML page."""
    import re

    match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
