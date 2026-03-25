"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # watchlists
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("tickers", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_watchlist_user_name"),
    )

    # score_history
    op.create_table(
        "score_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("scored_date", sa.Date(), nullable=False),
        sa.Column("profile", sa.String(10), nullable=False),
        sa.Column("total_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("fundamental", sa.Numeric(6, 2)),
        sa.Column("price_score", sa.Numeric(6, 2)),
        sa.Column("recommendation", sa.String(50)),
        sa.Column("breakdown", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "ticker", "scored_date", "profile", name="uq_score_history"),
    )
    op.create_index("idx_score_history_ticker_date", "score_history", ["ticker", "scored_date"])
    op.create_index("idx_score_history_user_date", "score_history", ["user_id", sa.text("scored_date DESC")])

    # alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("score_above", sa.Numeric(6, 2)),
        sa.Column("score_below", sa.Numeric(6, 2)),
        sa.Column("price_above", sa.Numeric(12, 2)),
        sa.Column("price_below", sa.Numeric(12, 2)),
        sa.Column("rsi_overbought", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("rsi_oversold", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "ticker", name="uq_alert_user_ticker"),
    )

    # market_data_cache
    op.create_table(
        "market_data_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False, index=True),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(12, 4)),
        sa.Column("high", sa.Numeric(12, 4)),
        sa.Column("low", sa.Numeric(12, 4)),
        sa.Column("close", sa.Numeric(12, 4), nullable=False),
        sa.Column("volume", sa.BigInteger()),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ticker", "trade_date", name="uq_mdc_ticker_date"),
    )

    # ticker_info_cache
    op.create_table(
        "ticker_info_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(20), unique=True, nullable=False),
        sa.Column("quote_type", sa.String(20)),
        sa.Column("info_json", JSONB, nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # industries
    op.create_table(
        "industries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("tickers", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("industries")
    op.drop_table("ticker_info_cache")
    op.drop_table("market_data_cache")
    op.drop_table("alerts")
    op.drop_index("idx_score_history_user_date", table_name="score_history")
    op.drop_index("idx_score_history_ticker_date", table_name="score_history")
    op.drop_table("score_history")
    op.drop_table("watchlists")
    op.drop_table("users")
