from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.market_data_cache import MarketDataCache
from backend.app.models.ticker_info_cache import TickerInfoCache
from backend.app.models.ticker_profile import TickerProfile


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
        """Return cached OHLC from `since` to latest, or None if all OHLC columns are present."""
        stmt = (
            select(
                MarketDataCache.trade_date,
                MarketDataCache.open,
                MarketDataCache.high,
                MarketDataCache.low,
                MarketDataCache.close,
            )
            .where(
                MarketDataCache.ticker == ticker,
                MarketDataCache.trade_date >= since,
                MarketDataCache.open.is_not(None),
                MarketDataCache.high.is_not(None),
                MarketDataCache.low.is_not(None),
            )
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
        has_ohlc = "Open" in df.columns and "High" in df.columns and "Low" in df.columns
        has_volume = "Volume" in df.columns
        for dt, row in df.iterrows():
            rows.append({
                "ticker": ticker,
                "trade_date": dt.date() if hasattr(dt, "date") else dt,
                "open": float(row["Open"]) if has_ohlc and pd.notna(row["Open"]) else None,
                "high": float(row["High"]) if has_ohlc and pd.notna(row["High"]) else None,
                "low": float(row["Low"]) if has_ohlc and pd.notna(row["Low"]) else None,
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if has_volume and pd.notna(row["Volume"]) else None,
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

    # --- Ticker Profile (name cache) ---

    async def get_ticker_profile(self, ticker: str) -> TickerProfile | None:
        stmt = select(TickerProfile).where(TickerProfile.ticker == ticker)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_ticker_by_name(self, name: str) -> str | None:
        normalized = name.strip()
        if not normalized:
            return None
        stmt = (
            select(TickerProfile.ticker)
            .where(
                or_(
                    func.lower(TickerProfile.name_zh) == normalized.lower(),
                    func.lower(TickerProfile.name_en) == normalized.lower(),
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_ticker_profile(
        self, ticker: str, name_zh: str | None, name_en: str | None, source: str
    ) -> None:
        now = datetime.now(timezone.utc)
        stmt = insert(TickerProfile).values(
            ticker=ticker,
            name_zh=name_zh,
            name_en=name_en,
            source=source,
            updated_at=now,
            last_used_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_={
                "name_zh": stmt.excluded.name_zh,
                "name_en": stmt.excluded.name_en,
                "source": stmt.excluded.source,
                "updated_at": stmt.excluded.updated_at,
                "last_used_at": stmt.excluded.last_used_at,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def touch_ticker_profile(self, ticker: str) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            insert(TickerProfile)
            .values(ticker=ticker, source="unknown", last_used_at=now, updated_at=now)
            .on_conflict_do_update(
                index_elements=["ticker"],
                set_={"last_used_at": now},
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
