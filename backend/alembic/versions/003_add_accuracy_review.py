"""Add price_at_score to score_history and create accuracy_review table

Revision ID: 003
Revises: 002
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add price_at_score column to score_history
    op.add_column(
        "score_history",
        sa.Column("price_at_score", sa.Numeric(12, 4), nullable=True),
    )

    # Create accuracy_review table
    op.create_table(
        "accuracy_review",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "score_history_id",
            sa.Integer,
            sa.ForeignKey("score_history.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(20), nullable=False, index=True),
        sa.Column("scored_date", sa.Date, nullable=False),
        sa.Column("profile", sa.String(10), nullable=False),
        sa.Column("review_days", sa.Integer, nullable=False),
        sa.Column("score_at_time", sa.Numeric(6, 2), nullable=False),
        sa.Column("recommendation", sa.String(50), nullable=False),
        sa.Column("price_at_score", sa.Numeric(12, 4), nullable=False),
        sa.Column("price_at_review", sa.Numeric(12, 4), nullable=False),
        sa.Column("return_pct", sa.Numeric(8, 4), nullable=False),
        sa.Column("is_accurate", sa.Boolean, nullable=False),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("score_history_id", "review_days", name="uq_accuracy_review"),
    )

    op.create_index("ix_accuracy_review_scored_date", "accuracy_review", ["scored_date"])
    op.create_index("ix_accuracy_review_profile_days", "accuracy_review", ["profile", "review_days"])


def downgrade() -> None:
    op.drop_table("accuracy_review")
    op.drop_column("score_history", "price_at_score")
