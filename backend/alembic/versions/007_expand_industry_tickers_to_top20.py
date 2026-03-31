"""Expand each industry ticker list to top 20

Revision ID: 007
Revises: 006
Create Date: 2026-03-31
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None

INDUSTRY_TOP_20 = {
    "半導體": [
        "2330.TW",
        "2454.TW",
        "2303.TW",
        "3711.TW",
        "3034.TW",
        "3443.TW",
        "5347.TWO",
        "4966.TW",
        "5269.TW",
        "6488.TW",
        "2408.TW",
        "2344.TW",
        "3105.TWO",
        "8086.TWO",
        "8299.TWO",
        "3014.TW",
        "3227.TWO",
        "6531.TW",
        "6515.TWO",
        "2363.TW",
    ],
    "金融": [
        "2881.TW",
        "2882.TW",
        "2884.TW",
        "2886.TW",
        "2891.TW",
        "2892.TW",
        "2880.TW",
        "2883.TW",
        "2885.TW",
        "2887.TW",
        "2888.TW",
        "2801.TW",
        "2834.TW",
        "2836.TW",
        "2845.TW",
        "5880.TW",
        "5876.TW",
        "6005.TW",
        "6024.TW",
        "2809.TW",
    ],
    "傳產": [
        "1301.TW",
        "1303.TW",
        "1326.TW",
        "2002.TW",
        "1216.TW",
        "2207.TW",
        "1101.TW",
        "1102.TW",
        "2603.TW",
        "2615.TW",
        "2618.TW",
        "6505.TW",
        "2912.TW",
        "9904.TW",
        "9945.TW",
        "2105.TW",
        "2106.TW",
        "1402.TW",
        "2201.TW",
        "9933.TW",
    ],
    "電子零組件": [
        "2317.TW",
        "2382.TW",
        "2308.TW",
        "2327.TW",
        "3231.TW",
        "3037.TW",
        "2356.TW",
        "2392.TW",
        "2324.TW",
        "6278.TW",
        "4915.TW",
        "3036.TW",
        "2383.TW",
        "3044.TW",
        "3008.TW",
        "2376.TW",
        "3017.TW",
        "3023.TW",
        "6414.TW",
        "3533.TW",
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
    for name, tickers in INDUSTRY_TOP_20.items():
        tickers_literal = "{" + ",".join(tickers) + "}"
        op.execute(
            sa.text(
                """
                UPDATE industries
                SET tickers = :tickers
                WHERE name = :name
                """
            ).bindparams(name=name, tickers=tickers_literal)
        )


def downgrade() -> None:
    pass
