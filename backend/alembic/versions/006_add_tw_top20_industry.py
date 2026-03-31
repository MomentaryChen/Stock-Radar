"""Add TW top 20 ranked tickers to industries

Revision ID: 006
Revises: 005
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

TOP_TW_20_TICKERS = [
    "2330.TW",  # TSMC
    "2454.TW",  # MediaTek
    "2317.TW",  # Hon Hai
    "2308.TW",  # Delta Electronics
    "2382.TW",  # Quanta Computer
    "2881.TW",  # Fubon Financial
    "2303.TW",  # UMC
    "3711.TW",  # ASE Technology
    "2412.TW",  # Chunghwa Telecom
    "2891.TW",  # CTBC Financial
    "2882.TW",  # Cathay Financial
    "2886.TW",  # Mega Financial
    "2884.TW",  # E.SUN Financial
    "1301.TW",  # Formosa Plastics
    "1303.TW",  # Nan Ya Plastics
    "2002.TW",  # China Steel
    "1216.TW",  # Uni-President
    "5880.TW",  # Taiwan Cooperative Financial
    "3045.TW",  # Taiwan Mobile
    "6505.TW",  # Formosa Petrochemical
]


def upgrade() -> None:
    tickers_literal = "{" + ",".join(TOP_TW_20_TICKERS) + "}"
    op.execute(
        sa.text(
            """
            INSERT INTO industries (name, tickers)
            VALUES (:name, :tickers)
            ON CONFLICT (name)
            DO UPDATE SET tickers = EXCLUDED.tickers
            """
        ).bindparams(name="台股排行", tickers=tickers_literal)
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM industries WHERE name = :name").bindparams(name="台股排行"))
