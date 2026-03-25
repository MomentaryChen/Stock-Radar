"""Seed industries and default user

Revision ID: 002
Revises: 001
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDUSTRIES = {
    "半導體": ["2330.TW", "2303.TW", "2454.TW", "3711.TW"],
    "金融": ["2881.TW", "2882.TW", "2884.TW", "2886.TW"],
    "傳產": ["1301.TW", "1303.TW", "2002.TW", "1326.TW"],
    "電子零組件": ["2317.TW", "2382.TW", "3008.TW"],
    "ETF": ["0050.TW", "0056.TW", "00878.TW", "00882.TW"],
}


def upgrade() -> None:
    # Default user
    op.execute(sa.text("INSERT INTO users (username) VALUES ('default') ON CONFLICT DO NOTHING"))

    # Seed industries
    for name, tickers in INDUSTRIES.items():
        tickers_literal = "{" + ",".join(tickers) + "}"
        op.execute(
            sa.text(
                "INSERT INTO industries (name, tickers) VALUES (:name, :tickers) ON CONFLICT DO NOTHING"
            ).bindparams(name=name, tickers=tickers_literal)
        )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM industries"))
    op.execute(sa.text("DELETE FROM users WHERE username = 'default'"))
