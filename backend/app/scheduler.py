"""APScheduler integration for periodic background jobs."""

import asyncio
import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.config import settings
from backend.app.db import async_session
from backend.app.repositories.industry_repo import IndustryRepo
from backend.app.services.accuracy_review_service import AccuracyReviewService
from backend.app.services.news_sentiment_service import NewsSentimentService
from backend.app.services.ticker_resolver_service import resolve_identifier_to_ticker

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_daily_accuracy_review() -> None:
    """Scheduled job: review accuracy for all windows (3d, 7d, 30d)."""
    logger.info("Starting scheduled accuracy review...")
    async with async_session() as session:
        svc = AccuracyReviewService(session)
        stats = await svc.run_review(today=date.today())
        logger.info("Scheduled accuracy review completed: %s", stats)


async def run_hourly_industry_news_refresh() -> None:
    """Scheduled job: refresh news for all tickers referenced by industries."""
    logger.info("Starting scheduled hourly industry news refresh...")
    async with async_session() as session:
        industry_repo = IndustryRepo(session)
        industries = await industry_repo.get_all()
        unique_tickers: set[str] = set()
        for industry in industries:
            for raw_ticker in industry.tickers:
                ticker = await resolve_identifier_to_ticker(session, raw_ticker)
                if ticker:
                    unique_tickers.add(ticker)

        if not unique_tickers:
            logger.info("Hourly industry news refresh skipped: no industry tickers found")
            return

        semaphore = asyncio.Semaphore(max(1, settings.news_scheduler_max_concurrency))

        async def _refresh_single_ticker(ticker: str) -> tuple[str, bool]:
            async with semaphore:
                try:
                    async with async_session() as ticker_session:
                        news_svc = NewsSentimentService(ticker_session)
                        await news_svc.get_news(
                            ticker=ticker,
                            limit=settings.news_scheduler_fetch_limit,
                            force_refresh=True,
                        )
                    return ticker, True
                except Exception:
                    logger.exception("Scheduled news refresh failed for ticker %s", ticker)
                    return ticker, False

        results = await asyncio.gather(
            *(_refresh_single_ticker(ticker) for ticker in sorted(unique_tickers))
        )

        success = sum(1 for _, ok in results if ok)
        failed = len(results) - success
        logger.info(
            "Scheduled hourly industry news refresh completed: total=%d success=%d failed=%d concurrency=%d",
            len(unique_tickers),
            success,
            failed,
            settings.news_scheduler_max_concurrency,
        )

        # Keep a compact warning line for quick log scanning.
        if failed > 0:
            failed_tickers = [ticker for ticker, ok in results if not ok]
            logger.warning("Hourly industry news refresh failed tickers: %s", failed_tickers)


def start_scheduler() -> None:
    """Register jobs and start the scheduler."""
    scheduler.add_job(
        run_daily_accuracy_review,
        trigger=CronTrigger(hour=18, minute=30),  # Run at 18:30 daily (after TW market close)
        id="daily_accuracy_review",
        name="Daily accuracy review",
        replace_existing=True,
    )
    if settings.news_scheduler_enabled:
        scheduler.add_job(
            run_hourly_industry_news_refresh,
            trigger=IntervalTrigger(hours=max(1, settings.news_scheduler_interval_hours)),
            id="hourly_industry_news_refresh",
            name="Hourly industry news refresh",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    scheduler.start()
    logger.info(
        "Scheduler started - daily accuracy review at 18:30, hourly industry news refresh=%s interval_hours=%d",
        settings.news_scheduler_enabled,
        settings.news_scheduler_interval_hours,
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
