"""Repository for accuracy review CRUD and aggregation queries."""

from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.accuracy_review import AccuracyReview
from backend.app.models.score_history import ScoreHistory


class AccuracyReviewRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pending_score_histories(
        self, review_days: int, today: date
    ) -> list[ScoreHistory]:
        """Find score_history rows that are exactly `review_days` old and not yet reviewed."""
        target_date = today - timedelta(days=review_days)

        already_reviewed = (
            select(AccuracyReview.score_history_id)
            .where(AccuracyReview.review_days == review_days)
            .scalar_subquery()
        )

        stmt = (
            select(ScoreHistory)
            .where(
                ScoreHistory.scored_date <= target_date,
                ScoreHistory.price_at_score.is_not(None),
                ScoreHistory.id.not_in(already_reviewed),
            )
            .order_by(ScoreHistory.scored_date)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        score_history_id: int,
        ticker: str,
        scored_date: date,
        profile: str,
        review_days: int,
        score_at_time: float,
        recommendation: str,
        price_at_score: float,
        price_at_review: float,
        return_pct: float,
        is_accurate: bool,
    ) -> None:
        stmt = insert(AccuracyReview).values(
            score_history_id=score_history_id,
            ticker=ticker,
            scored_date=scored_date,
            profile=profile,
            review_days=review_days,
            score_at_time=score_at_time,
            recommendation=recommendation,
            price_at_score=price_at_score,
            price_at_review=price_at_review,
            return_pct=return_pct,
            is_accurate=is_accurate,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_accuracy_review",
            set_={
                "price_at_review": stmt.excluded.price_at_review,
                "return_pct": stmt.excluded.return_pct,
                "is_accurate": stmt.excluded.is_accurate,
                "reviewed_at": func.now(),
            },
        )
        await self.session.execute(stmt)

    async def flush(self) -> None:
        await self.session.commit()

    async def get_summary(
        self,
        profile: str | None = None,
        review_days: int | None = None,
    ) -> list[dict]:
        """Aggregate accuracy stats grouped by profile and review_days."""
        stmt = select(
            AccuracyReview.profile,
            AccuracyReview.review_days,
            func.count().label("total_reviews"),
            func.sum(case((AccuracyReview.is_accurate.is_(True), 1), else_=0)).label("accurate_count"),
            func.avg(AccuracyReview.return_pct).label("avg_return_pct"),
            func.min(AccuracyReview.scored_date).label("earliest_scored_date"),
            func.max(AccuracyReview.scored_date).label("latest_scored_date"),
        ).group_by(AccuracyReview.profile, AccuracyReview.review_days)

        if profile:
            stmt = stmt.where(AccuracyReview.profile == profile)
        if review_days:
            stmt = stmt.where(AccuracyReview.review_days == review_days)

        stmt = stmt.order_by(AccuracyReview.profile, AccuracyReview.review_days)
        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {
                "profile": r.profile,
                "review_days": r.review_days,
                "total_reviews": r.total_reviews,
                "accurate_count": r.accurate_count,
                "accuracy_rate": round(r.accurate_count / r.total_reviews, 4) if r.total_reviews > 0 else 0,
                "avg_return_pct": round(float(r.avg_return_pct), 4) if r.avg_return_pct else 0,
                "earliest_scored_date": str(r.earliest_scored_date),
                "latest_scored_date": str(r.latest_scored_date),
            }
            for r in rows
        ]

    async def get_details(
        self,
        profile: str | None = None,
        review_days: int | None = None,
        ticker: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Return per-record accuracy details."""
        stmt = (
            select(AccuracyReview)
            .order_by(AccuracyReview.reviewed_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if profile:
            stmt = stmt.where(AccuracyReview.profile == profile)
        if review_days:
            stmt = stmt.where(AccuracyReview.review_days == review_days)
        if ticker:
            stmt = stmt.where(AccuracyReview.ticker == ticker)

        result = await self.session.execute(stmt)
        rows = result.scalars().all()

        return [
            {
                "id": r.id,
                "ticker": r.ticker,
                "scored_date": str(r.scored_date),
                "profile": r.profile,
                "review_days": r.review_days,
                "score_at_time": float(r.score_at_time),
                "recommendation": r.recommendation,
                "price_at_score": float(r.price_at_score),
                "price_at_review": float(r.price_at_review),
                "return_pct": float(r.return_pct),
                "is_accurate": r.is_accurate,
                "reviewed_at": r.reviewed_at.isoformat(),
            }
            for r in rows
        ]
