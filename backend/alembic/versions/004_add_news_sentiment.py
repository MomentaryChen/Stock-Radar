"""Create news_sentiment table

Revision ID: 004
Revises: 003
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_sentiment",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("publisher", sa.String(200), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("sentiment_label", sa.String(10), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("url", name="uq_news_url"),
    )

    op.create_index("ix_news_sentiment_published_at", "news_sentiment", ["published_at"])


def downgrade() -> None:
    op.drop_table("news_sentiment")
