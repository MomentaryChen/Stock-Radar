"""News sentiment service: fetch Yahoo Finance news, analyze, and cache."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.models.news_sentiment import NewsSentiment
from backend.app.repositories.news_sentiment_repo import NewsSentimentRepo
from backend.core.sentiment import analyze_news_batch

logger = logging.getLogger(__name__)


def _fetch_yfinance_news(ticker: str) -> list[dict]:
    """Synchronous helper to fetch news from yfinance."""
    import yfinance as yf

    t = yf.Ticker(ticker)
    news = t.news
    if not news:
        return []
    return news


def _extract_url(item: dict) -> str:
    """Extract a stable URL for deduplication across yfinance news shapes."""
    url = item.get("link") or ""
    if url:
        return url
    content = item.get("content") or {}
    for k in ("canonicalUrl", "clickThroughUrl"):
        u = (content.get(k) or {}).get("url")
        if u:
            return u
    return ""


class NewsSentimentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NewsSentimentRepo(session)

    async def get_news(
        self,
        ticker: str,
        limit: int = 20,
        force_refresh: bool = False,
    ) -> list[NewsSentiment]:
        """Fetch, analyze, and return news for a ticker.

        Uses DB cache with TTL to avoid redundant Yahoo Finance calls.
        Uses URL deduplication to avoid re-analyzing the same article.
        """
        if not force_refresh:
            last_fetched = await self.repo.get_latest_fetched_at(ticker)
            if last_fetched is not None:
                age = datetime.now(timezone.utc) - last_fetched.replace(tzinfo=timezone.utc)
                if age < timedelta(hours=settings.news_cache_ttl_hours):
                    return await self.repo.get_by_ticker(ticker, limit)

        # Fetch from Yahoo Finance in a thread (yfinance is synchronous)
        try:
            raw_news = await asyncio.to_thread(_fetch_yfinance_news, ticker)
        except Exception:
            logger.exception("Failed to fetch news for %s", ticker)
            raw_news = []

        if raw_news:
            # Deduplicate: skip URLs already in DB
            urls = [u for u in (_extract_url(item) for item in raw_news) if u]
            existing_urls = await self.repo.get_existing_urls(urls)
            new_items = [item for item in raw_news if _extract_url(item) and _extract_url(item) not in existing_urls]

            if new_items:
                analyzed = analyze_news_batch(ticker, new_items)
                await self.repo.bulk_insert(analyzed)

        return await self.repo.get_by_ticker(ticker, limit)
