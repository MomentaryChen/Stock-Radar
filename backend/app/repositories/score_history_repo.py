from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.score_history import ScoreHistory


class ScoreHistoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        user_id: int,
        ticker: str,
        scored_date: date,
        profile: str,
        total_score: float,
        fundamental: float | None,
        price_score: float | None,
        recommendation: str | None,
        breakdown: dict | None = None,
        price_at_score: float | None = None,
    ) -> None:
        stmt = insert(ScoreHistory).values(
            user_id=user_id,
            ticker=ticker,
            scored_date=scored_date,
            profile=profile,
            total_score=total_score,
            fundamental=fundamental,
            price_score=price_score,
            recommendation=recommendation,
            breakdown=breakdown,
            price_at_score=price_at_score,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_score_history",
            set_={
                "total_score": stmt.excluded.total_score,
                "fundamental": stmt.excluded.fundamental,
                "price_score": stmt.excluded.price_score,
                "recommendation": stmt.excluded.recommendation,
                "breakdown": stmt.excluded.breakdown,
                "price_at_score": stmt.excluded.price_at_score,
            },
        )
        await self.session.execute(stmt)

    async def get_previous_scores(
        self, user_id: int, profile: str, before_date: date
    ) -> dict[str, float]:
        """Return {ticker: total_score} for the most recent scored_date before `before_date`."""
        sub = (
            select(ScoreHistory.scored_date)
            .where(
                ScoreHistory.user_id == user_id,
                ScoreHistory.profile == profile,
                ScoreHistory.scored_date < before_date,
            )
            .order_by(ScoreHistory.scored_date.desc())
            .limit(1)
            .scalar_subquery()
        )
        stmt = select(ScoreHistory.ticker, ScoreHistory.total_score).where(
            ScoreHistory.user_id == user_id,
            ScoreHistory.profile == profile,
            ScoreHistory.scored_date == sub,
        )
        result = await self.session.execute(stmt)
        return {row[0]: float(row[1]) for row in result.all()}

    async def flush(self) -> None:
        await self.session.commit()
