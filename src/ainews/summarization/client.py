"""Claude API client wrapper."""

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential


class ClaudeClient:
    """Wrapper for the Anthropic Claude API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key.
            model: Model to use for generation.
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
    )
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> tuple[str, int]:
        """Generate a response from Claude.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.

        Returns:
            Tuple of (response text, tokens used).
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)

        # Extract text from response
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text

        # Calculate total tokens
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return text, tokens_used
