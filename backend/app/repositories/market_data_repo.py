from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.market_data_cache import MarketDataCache
from backend.app.models.ticker_info_cache import TickerInfoCache


class MarketDataRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_close_series(self, ticker: str, since: date) -> pd.Series | None:
        """Return cached close series from `since` to latest, or None if insufficient."""
        stmt = (
            select(MarketDataCache.trade_date, MarketDataCache.close)
            .where(MarketDataCache.ticker == ticker, MarketDataCache.trade_date >= since)
            .order_by(MarketDataCache.trade_date)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        if not rows:
            return None
        dates, closes = zip(*rows)
        return pd.Series(data=[float(c) for c in closes], index=pd.DatetimeIndex(dates), name="Close")

    async def get_ohlc(self, ticker: str, since: date) -> pd.DataFrame | None:
        """Return cached OHLC from `since` to latest, or None if insufficient."""
        stmt = (
            select(
                MarketDataCache.trade_date,
                MarketDataCache.open,
                MarketDataCache.high,
                MarketDataCache.low,
                MarketDataCache.close,
            )
            .where(MarketDataCache.ticker == ticker, MarketDataCache.trade_date >= since)
            .order_by(MarketDataCache.trade_date)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        if not rows:
            return None
        data = [
            {"Open": float(r[1]), "High": float(r[2]), "Low": float(r[3]), "Close": float(r[4])}
            for r in rows
        ]
        return pd.DataFrame(data, index=pd.DatetimeIndex([r[0] for r in rows]))

    async def get_last_fetched_at(self, ticker: str) -> datetime | None:
        """Return the most recent fetched_at for a ticker."""
        stmt = (
            select(MarketDataCache.fetched_at)
            .where(MarketDataCache.ticker == ticker)
            .order_by(MarketDataCache.fetched_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def upsert_ohlc_rows(self, ticker: str, df: pd.DataFrame) -> None:
        """Bulk upsert OHLC data from a pandas DataFrame."""
        now = datetime.now(timezone.utc)
        rows = []
        for dt, row in df.iterrows():
            rows.append({
                "ticker": ticker,
                "trade_date": dt.date() if hasattr(dt, "date") else dt,
                "open": float(row.get("Open", 0)) if pd.notna(row.get("Open")) else None,
                "high": float(row.get("High", 0)) if pd.notna(row.get("High")) else None,
                "low": float(row.get("Low", 0)) if pd.notna(row.get("Low")) else None,
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if "Volume" in row and pd.notna(row.get("Volume")) else None,
                "fetched_at": now,
            })
        if not rows:
            return
        stmt = insert(MarketDataCache).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_mdc_ticker_date",
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()

    # --- Ticker Info ---

    async def get_ticker_info(self, ticker: str, ttl_hours: int = 24) -> dict | None:
        """Return cached info if fresh enough, else None."""
        stmt = select(TickerInfoCache).where(TickerInfoCache.ticker == ticker)
        result = await self.session.execute(stmt)
        cached = result.scalar_one_or_none()
        if cached is None:
            return None
        age = datetime.now(timezone.utc) - cached.fetched_at.replace(tzinfo=timezone.utc)
        if age > timedelta(hours=ttl_hours):
            return None
        return cached.info_json

    async def upsert_ticker_info(self, ticker: str, info: dict) -> None:
        quote_type = str(info.get("quoteType", "EQUITY")).upper()
        stmt = insert(TickerInfoCache).values(
            ticker=ticker, quote_type=quote_type, info_json=info, fetched_at=datetime.now(timezone.utc)
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_={
                "quote_type": stmt.excluded.quote_type,
                "info_json": stmt.excluded.info_json,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()
