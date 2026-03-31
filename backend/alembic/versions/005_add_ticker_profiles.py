"""Create ticker_profiles table

Revision ID: 005
Revises: 004
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticker_profiles",
        sa.Column("ticker", sa.String(20), primary_key=True),
        sa.Column("name_zh", sa.String(255), nullable=True),
        sa.Column("name_en", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ticker_profiles_last_used_at", "ticker_profiles", ["last_used_at"])


def downgrade() -> None:
    op.drop_index("ix_ticker_profiles_last_used_at", table_name="ticker_profiles")
    op.drop_table("ticker_profiles")
