"""Article deduplication."""

from ainews.models.article import Article


class Deduplicator:
    """Deduplicates articles based on URL and content hash."""

    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize the deduplicator.

        Args:
            similarity_threshold: Threshold for content similarity (0-1).
                Articles with similarity above this are considered duplicates.
        """
        self.similarity_threshold = similarity_threshold

    def deduplicate(
        self,
        new_articles: list[Article],
        existing_articles: list[Article] | None = None,
    ) -> list[Article]:
        """Remove duplicate articles.

        Args:
            new_articles: List of newly fetched articles.
            existing_articles: Optional list of existing articles to check against.

        Returns:
            List of unique articles not present in existing_articles.
        """
        if not new_articles:
            return []

        existing_articles = existing_articles or []

        # Build sets for fast lookup
        existing_ids = {a.id for a in existing_articles}
        existing_hashes = {a.content_hash for a in existing_articles if a.content_hash}

        unique_articles: list[Article] = []
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()

        for article in new_articles:
            # Skip if URL already seen (same article ID)
            if article.id in existing_ids or article.id in seen_ids:
                continue

            # Skip if content hash matches (duplicate content)
            if article.content_hash:
                if article.content_hash in existing_hashes or article.content_hash in seen_hashes:
                    continue

            # Article is unique
            unique_articles.append(article)
            seen_ids.add(article.id)
            if article.content_hash:
                seen_hashes.add(article.content_hash)

        return unique_articles

    def find_similar(
        self,
        article: Article,
        candidates: list[Article],
    ) -> list[Article]:
        """Find articles similar to the given article.

        Uses a simple word overlap metric for similarity.

        Args:
            article: The article to compare against.
            candidates: List of candidate articles to check.

        Returns:
            List of similar articles above the similarity threshold.
        """
        if not article.content:
            return []

        article_words = set(article.content.lower().split())
        similar = []

        for candidate in candidates:
            if not candidate.content or candidate.id == article.id:
                continue

            candidate_words = set(candidate.content.lower().split())

            # Calculate Jaccard similarity
            intersection = len(article_words & candidate_words)
            union = len(article_words | candidate_words)

            if union > 0:
                similarity = intersection / union
                if similarity >= self.similarity_threshold:
                    similar.append(candidate)

        return similar
