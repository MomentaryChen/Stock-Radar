"""APScheduler integration for periodic accuracy reviews."""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.app.db import async_session
from backend.app.services.accuracy_review_service import AccuracyReviewService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_daily_accuracy_review() -> None:
    """Scheduled job: review accuracy for all windows (3d, 7d, 30d)."""
    logger.info("Starting scheduled accuracy review...")
    async with async_session() as session:
        svc = AccuracyReviewService(session)
        stats = await svc.run_review(today=date.today())
        logger.info("Scheduled accuracy review completed: %s", stats)


def start_scheduler() -> None:
    """Register jobs and start the scheduler."""
    scheduler.add_job(
        run_daily_accuracy_review,
        trigger=CronTrigger(hour=18, minute=30),  # Run at 18:30 daily (after TW market close)
        id="daily_accuracy_review",
        name="Daily accuracy review",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started - accuracy review scheduled daily at 18:30")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
