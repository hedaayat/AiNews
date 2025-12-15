"""Initial schema creation.

Revision ID: 001
Revises:
Create Date: 2025-12-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create sources table
    op.create_table(
        "sources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("enabled", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "last_fetched",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column("fetch_interval_hours", sa.Integer(), nullable=True),
        sa.Column(
            "added_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create articles table
    op.create_table(
        "articles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(
        "idx_articles_published",
        "articles",
        ["published_at"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_articles_source",
        "articles",
        ["source_id"],
        postgresql_using="btree",
    )

    # Create summaries table
    op.create_table(
        "summaries",
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("key_topics", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("article_count", sa.Integer(), nullable=False),
        sa.Column("article_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("model_used", sa.String(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("date"),
    )

    # Create notable_stories table
    op.create_table(
        "notable_stories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("summary_date", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["summary_date"],
            ["summaries.date"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_notable_stories_date",
        "notable_stories",
        ["summary_date"],
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("idx_notable_stories_date", table_name="notable_stories")
    op.drop_table("notable_stories")
    op.drop_table("summaries")
    op.drop_index("idx_articles_source", table_name="articles")
    op.drop_index("idx_articles_published", table_name="articles")
    op.drop_table("articles")
    op.drop_table("sources")
