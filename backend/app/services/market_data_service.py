"""Market data service: yfinance fetch with DB cache layer."""

import asyncio
from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.repositories.market_data_repo import MarketDataRepo
from backend.core import data as core_data

# Period string to approximate number of calendar days
_PERIOD_DAYS = {
    "1y": 365,
    "2y": 730,
    "3y": 1095,
    "5y": 1825,
}


def _period_to_since(period: str) -> date:
    days = _PERIOD_DAYS.get(period, 365)
    return (datetime.now(timezone.utc) - timedelta(days=days)).date()


class MarketDataService:
    def __init__(self, session: AsyncSession):
        self.repo = MarketDataRepo(session)

    async def get_close_series(self, ticker: str, period: str) -> pd.Series:
        since = _period_to_since(period)

        # Check if cache is fresh
        last_fetched = await self.repo.get_last_fetched_at(ticker)
        cache_fresh = (
            last_fetched is not None
            and (datetime.now(timezone.utc) - last_fetched.replace(tzinfo=timezone.utc))
            < timedelta(minutes=settings.market_data_cache_ttl_minutes)
        )

        if cache_fresh:
            cached = await self.repo.get_close_series(ticker, since)
            if cached is not None and len(cached) > 10:
                return cached

        # Cache miss or stale — fetch from yfinance
        close = await asyncio.to_thread(core_data.fetch_close_series, ticker, period)

        # Write to cache (build a minimal DataFrame for upsert)
        cache_df = pd.DataFrame({"Close": close})
        await self.repo.upsert_ohlc_rows(ticker, cache_df)

        return close

    async def get_ohlc(self, ticker: str, period: str) -> pd.DataFrame:
        since = _period_to_since(period)

        last_fetched = await self.repo.get_last_fetched_at(ticker)
        cache_fresh = (
            last_fetched is not None
            and (datetime.now(timezone.utc) - last_fetched.replace(tzinfo=timezone.utc))
            < timedelta(minutes=settings.market_data_cache_ttl_minutes)
        )

        if cache_fresh:
            cached = await self.repo.get_ohlc(ticker, since)
            if cached is not None and len(cached) > 10:
                return cached

        ohlc = await asyncio.to_thread(core_data.fetch_ohlc, ticker, period)
        await self.repo.upsert_ohlc_rows(ticker, ohlc)
        return ohlc

    async def get_ticker_info(self, ticker: str) -> dict:
        cached = await self.repo.get_ticker_info(ticker, settings.ticker_info_cache_ttl_hours)
        if cached is not None:
            return cached

        info = await asyncio.to_thread(core_data.fetch_ticker_info, ticker)
        await self.repo.upsert_ticker_info(ticker, info)
        return info
