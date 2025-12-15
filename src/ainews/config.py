"""Configuration management for AI News Aggregator."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AINEWS_",
        env_file_encoding="utf-8",
    )

    # API Keys
    anthropic_api_key: str = Field(description="Anthropic API key for Claude")

    # Email Configuration
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    email_from: str = Field(default="", description="Sender email address")
    email_to: str = Field(
        default="",
        description="Comma-separated recipient email addresses (e.g., 'user1@example.com,user2@example.com')"
    )

    @property
    def email_to_list(self) -> list[str]:
        """Parse email_to string into a list."""
        if not self.email_to:
            return []
        return [email.strip() for email in self.email_to.split(",")]

    # Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")

    # Claude Settings
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use for summarization",
    )
    max_articles_per_summary: int = Field(
        default=50,
        description="Maximum articles to include in a summary",
    )

    # Fetching Settings
    fetch_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    user_agent: str = Field(
        default="AiNews/1.0 (+https://github.com/ainews)",
        description="User agent for HTTP requests",
    )
    max_concurrent_fetches: int = Field(
        default=10,
        description="Maximum concurrent fetch operations",
    )

    # Database Settings
    database_url: str = Field(
        default="postgresql+asyncpg://localhost/ainews",
        description="PostgreSQL database URL (async)",
    )

    # Web Settings
    web_host: str = Field(default="0.0.0.0", description="Web server host")
    web_port: int = Field(default=8000, description="Web server port")
    environment: str = Field(default="development", description="Environment (development/production)")
    allow_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated, e.g., 'https://example.com,https://www.example.com')",
    )

    @property
    def allow_origins_list(self) -> list[str]:
        """Parse allow_origins string into a list."""
        if self.allow_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allow_origins.split(",")]

    @property
    def sources_file(self) -> Path:
        """Path to sources JSON file."""
        return self.data_dir / "sources.json"

    @property
    def articles_dir(self) -> Path:
        """Directory for article JSON files."""
        return self.data_dir / "articles"

    @property
    def summaries_dir(self) -> Path:
        """Directory for summary JSON files."""
        return self.data_dir / "summaries"

    def ensure_directories(self) -> None:
        """Create data directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.summaries_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
