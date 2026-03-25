"""
One-time migration: import localStorage JSON export into PostgreSQL.

Usage:
    python -m backend.scripts.migrate_localstorage <path_to_export.json>

The JSON file should have this structure (exported from the Streamlit app):
{
    "tw_stock_watchlists": {"核心持股": ["2330.TW"], ...},
    "tw_stock_score_history": {"2026-03-25": {"2330.TW": 65.5, ...}, ...},
    "tw_stock_alerts": {"2330.TW": {"score_above": 65, ...}, ...}
}
"""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.config import settings
from backend.app.models.alert import Alert
from backend.app.models.score_history import ScoreHistory
from backend.app.models.watchlist import Watchlist

DEFAULT_USER_ID = 1


async def migrate(data: dict) -> None:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # --- Watchlists ---
        watchlists = data.get("tw_stock_watchlists", {})
        if watchlists:
            print(f"Migrating {len(watchlists)} watchlists...")
            for name, tickers in watchlists.items():
                if not tickers:
                    continue
                wl = Watchlist(user_id=DEFAULT_USER_ID, name=name, tickers=tickers)
                session.add(wl)
            await session.commit()
            print("  Watchlists done.")

        # --- Score History ---
        score_history = data.get("tw_stock_score_history", {})
        if score_history:
            count = 0
            print(f"Migrating score history for {len(score_history)} dates...")
            for date_str, scores in score_history.items():
                scored_date = date.fromisoformat(date_str)
                for ticker, total_score in scores.items():
                    sh = ScoreHistory(
                        user_id=DEFAULT_USER_ID,
                        ticker=ticker,
                        scored_date=scored_date,
                        profile="平衡",
                        total_score=round(float(total_score), 2),
                    )
                    session.add(sh)
                    count += 1
            await session.commit()
            print(f"  {count} score records done.")

        # --- Alerts ---
        alerts = data.get("tw_stock_alerts", {})
        if alerts:
            print(f"Migrating {len(alerts)} alerts...")
            for ticker, config in alerts.items():
                alert = Alert(
                    user_id=DEFAULT_USER_ID,
                    ticker=ticker,
                    score_above=config.get("score_above"),
                    score_below=config.get("score_below"),
                    price_above=config.get("price_above"),
                    price_below=config.get("price_below"),
                    rsi_overbought=config.get("rsi_overbought", True),
                    rsi_oversold=config.get("rsi_oversold", True),
                )
                session.add(alert)
            await session.commit()
            print("  Alerts done.")

    await engine.dispose()
    print("Migration complete!")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m backend.scripts.migrate_localstorage <export.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    asyncio.run(migrate(data))


if __name__ == "__main__":
    main()
