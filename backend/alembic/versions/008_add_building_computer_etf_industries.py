"""Add building and computer-peripheral industries, update ETF list

Revision ID: 008
Revises: 007
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

INDUSTRY_TICKERS = {
    "建築": [
        "2542.TW",
        "2520.TW",
        "2538.TW",
        "2528.TW",
        "5534.TW",
        "6177.TW",
        "5515.TW",
        "5508.TW",
        "5522.TW",
        "2545.TW",
        "2511.TW",
        "2504.TW",
        "2515.TW",
        "2530.TW",
        "2516.TW",
        "2527.TW",
        "6171.TW",
        "6212.TW",
        "9946.TW",
        "1805.TW",
    ],
    "電腦周邊": [
        "3231.TW",
        "2382.TW",
        "2357.TW",
        "2376.TW",
        "2377.TW",
        "2465.TW",
        "3017.TW",
        "3211.TW",
        "3022.TW",
        "3046.TW",
        "2324.TW",
        "2495.TW",
        "4938.TW",
        "3005.TW",
        "3013.TW",
        "6128.TW",
        "4916.TW",
        "6669.TW",
        "3653.TW",
        "2301.TW",
    ],
    "ETF": [
        "0050.TW",
        "0056.TW",
        "00878.TW",
        "006208.TW",
        "00919.TW",
        "00929.TW",
        "00940.TW",
        "00692.TW",
        "00881.TW",
        "00713.TW",
        "00757.TW",
        "00850.TW",
        "0052.TW",
        "00646.TW",
        "00861.TW",
        "00631L.TW",
        "00632R.TW",
        "00730.TW",
        "00882.TW",
        "0051.TW",
    ],
}


def upgrade() -> None:
    for name, tickers in INDUSTRY_TICKERS.items():
        tickers_literal = "{" + ",".join(tickers) + "}"
        op.execute(
            sa.text(
                """
                INSERT INTO industries (name, tickers)
                VALUES (:name, :tickers)
                ON CONFLICT (name)
                DO UPDATE SET tickers = EXCLUDED.tickers
                """
            ).bindparams(name=name, tickers=tickers_literal)
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM industries
            WHERE name IN ('建築', '電腦周邊')
            """
        )
    )
