"""Service that reviews past scoring accuracy by comparing predicted vs actual prices."""

import logging
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.accuracy_review_repo import AccuracyReviewRepo
from backend.app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

REVIEW_WINDOWS = [3, 7, 30]

# Recommendation thresholds (mirrors core/scoring.py)
RECOMMEND_THRESHOLD = 65.0
NEUTRAL_THRESHOLD = 55.0


def _determine_accuracy(recommendation: str, return_pct: float) -> bool:
    """Determine if a recommendation was accurate based on actual return.

    - Recommend (score >= 65): accurate if price went up (return > 0)
    - Hold/conservative (score < 55): accurate if price went down or flat (return <= 0)
    - Neutral (55-64): accurate if absolute return is small (< 3%) or direction matched
    """
    if "推薦" in recommendation or "核心" in recommendation:
        return return_pct > 0
    if "保守" in recommendation or "觀望" in recommendation:
        return return_pct <= 0
    # Neutral: consider accurate if the move is modest or positive
    return abs(return_pct) < 0.03 or return_pct > 0


class AccuracyReviewService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AccuracyReviewRepo(session)
        self.mds = MarketDataService(session)

    async def run_review(self, today: date | None = None) -> dict:
        """Run accuracy review for all windows (3d, 7d, 30d).

        Finds score_history records old enough for each window,
        fetches the closing price at review date, and records accuracy.
        """
        today = today or date.today()
        stats = {}

        for days in REVIEW_WINDOWS:
            reviewed, skipped, errors = 0, 0, 0
            pending = await self.repo.get_pending_score_histories(days, today)

            for sh in pending:
                try:
                    review_date = sh.scored_date + timedelta(days=days)

                    # Get closing price on or near the review date
                    review_price = await self._get_close_on_or_near(
                        sh.ticker, review_date, today
                    )
                    if review_price is None:
                        skipped += 1
                        continue

                    price_at_score = float(sh.price_at_score)
                    return_pct = (review_price - price_at_score) / price_at_score
                    is_accurate = _determine_accuracy(sh.recommendation, return_pct)

                    await self.repo.upsert(
                        score_history_id=sh.id,
                        ticker=sh.ticker,
                        scored_date=sh.scored_date,
                        profile=sh.profile,
                        review_days=days,
                        score_at_time=float(sh.total_score),
                        recommendation=sh.recommendation,
                        price_at_score=price_at_score,
                        price_at_review=review_price,
                        return_pct=round(return_pct, 6),
                        is_accurate=is_accurate,
                    )
                    reviewed += 1
                except Exception as exc:
                    logger.warning("Accuracy review failed for %s: %s", sh.ticker, exc)
                    errors += 1

            await self.repo.flush()
            stats[f"{days}d"] = {"reviewed": reviewed, "skipped": skipped, "errors": errors}
            logger.info(
                "Accuracy review %dd: reviewed=%d skipped=%d errors=%d",
                days, reviewed, skipped, errors,
            )

        return stats

    async def _get_close_on_or_near(
        self, ticker: str, target_date: date, today: date
    ) -> float | None:
        """Get the closing price on target_date, or the nearest trading day within 3 days."""
        if target_date > today:
            return None

        # Fetch recent close series covering the target date window
        start = target_date - timedelta(days=5)
        close_series = await self.mds.get_close_series(ticker, "1y")
        if close_series is None or close_series.empty:
            return None

        # Find the closest trading day to target_date
        for offset in range(4):  # target_date, +1, +2, +3
            check = target_date + timedelta(days=offset)
            if check > today:
                break
            matches = close_series[close_series.index.date == check]
            if not matches.empty:
                return float(matches.iloc[0])

        # Try looking backwards
        for offset in range(1, 4):
            check = target_date - timedelta(days=offset)
            matches = close_series[close_series.index.date == check]
            if not matches.empty:
                return float(matches.iloc[0])

        return None

    async def get_summary(
        self, profile: str | None = None, review_days: int | None = None
    ) -> list[dict]:
        return await self.repo.get_summary(profile=profile, review_days=review_days)

    async def get_details(
        self,
        profile: str | None = None,
        review_days: int | None = None,
        ticker: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        return await self.repo.get_details(
            profile=profile, review_days=review_days, ticker=ticker,
            limit=limit, offset=offset,
        )
