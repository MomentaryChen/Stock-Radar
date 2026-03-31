"""News sentiment service: fetch Yahoo Finance news, analyze, and cache."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import requests
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


def _fetch_yahoo_rss_news(ticker: str) -> list[dict]:
    """Fetch Yahoo Finance RSS as fallback when yfinance returns empty."""
    endpoints = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
        f"https://finance.yahoo.com/rss/headline?s={ticker}",
    ]

    for url in endpoints:
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            root = ET.fromstring(response.text)
        except Exception:
            continue

        parsed_items: list[dict] = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            publisher = (item.findtext("source") or "Yahoo Finance").strip()
            pub_date_raw = (item.findtext("pubDate") or "").strip()

            publish_ts: int | None = None
            if pub_date_raw:
                try:
                    dt_obj = parsedate_to_datetime(pub_date_raw)
                    if dt_obj.tzinfo is None:
                        dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                    publish_ts = int(dt_obj.timestamp())
                except Exception:
                    publish_ts = None

            if not title or not link:
                continue

            parsed_items.append(
                {
                    "title": title,
                    "link": link,
                    "publisher": publisher,
                    "providerPublishTime": publish_ts,
                }
            )

        if parsed_items:
            return parsed_items

    return []


def _build_news_ticker_candidates(ticker: str) -> list[str]:
    """Build ticker candidates for Yahoo Finance news fallback."""
    normalized = ticker.strip().upper()
    if not normalized:
        return []

    candidates: list[str] = [normalized]
    base_symbol = normalized

    if normalized.endswith(".TW"):
        base_symbol = normalized[:-3]
        candidates.append(f"{base_symbol}.TWO")
    elif normalized.endswith(".TWO"):
        base_symbol = normalized[:-4]
        candidates.append(f"{base_symbol}.TW")

    if base_symbol and "." not in base_symbol:
        candidates.append(base_symbol)

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            deduped.append(candidate)

    return deduped


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

        # Fetch from all supported sources and ticker variants, then merge.
        ticker_candidates = _build_news_ticker_candidates(ticker)
        merged_raw_news: list[dict] = []

        # Layer 1: yfinance API
        for ticker_candidate in ticker_candidates:
            try:
                candidate_news = await asyncio.to_thread(_fetch_yfinance_news, ticker_candidate)
            except Exception:
                logger.exception("Failed to fetch news for %s", ticker_candidate)
                continue

            if candidate_news:
                merged_raw_news.extend(candidate_news)
                logger.info(
                    "Fetched %d yfinance news items for %s via ticker %s",
                    len(candidate_news),
                    ticker,
                    ticker_candidate,
                )

        # Layer 2: Yahoo RSS backup (always fetch and merge for better coverage)
        for ticker_candidate in ticker_candidates:
            try:
                candidate_news = await asyncio.to_thread(_fetch_yahoo_rss_news, ticker_candidate)
            except Exception:
                logger.exception("Failed to fetch RSS news for %s", ticker_candidate)
                continue

            if candidate_news:
                merged_raw_news.extend(candidate_news)
                logger.info(
                    "Fetched %d RSS news items for %s via ticker %s",
                    len(candidate_news),
                    ticker,
                    ticker_candidate,
                )

        if merged_raw_news:
            # In-memory dedup before DB check to reduce repeated URL lookups.
            deduped_raw_news: list[dict] = []
            seen_urls: set[str] = set()
            for item in merged_raw_news:
                url = _extract_url(item)
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                deduped_raw_news.append(item)

            # Keep only recent news (last 14 days) to avoid stale sentiment noise.
            recency_cutoff = datetime.now(timezone.utc) - timedelta(days=14)
            recent_raw_news: list[dict] = []
            for item in deduped_raw_news:
                publish_ts = item.get("providerPublishTime")
                if publish_ts is None:
                    recent_raw_news.append(item)
                    continue
                try:
                    published_at = datetime.fromtimestamp(publish_ts, tz=timezone.utc)
                except Exception:
                    recent_raw_news.append(item)
                    continue
                if published_at >= recency_cutoff:
                    recent_raw_news.append(item)

            # Deduplicate: skip URLs already in DB
            urls = [u for u in (_extract_url(item) for item in recent_raw_news) if u]
            existing_urls = await self.repo.get_existing_urls(urls)
            new_items = [
                item
                for item in recent_raw_news
                if _extract_url(item) and _extract_url(item) not in existing_urls
            ]

            if new_items:
                analyzed = analyze_news_batch(ticker, new_items)
                await self.repo.bulk_insert(analyzed)

        return await self.repo.get_by_ticker(ticker, limit)
