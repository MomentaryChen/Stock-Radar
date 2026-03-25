"""Repository for news_sentiment table."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.news_sentiment import NewsSentiment


class NewsSentimentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_ticker(self, ticker: str, limit: int = 20) -> list[NewsSentiment]:
        """Return recent news for a ticker, ordered by publish time descending."""
        stmt = (
            select(NewsSentiment)
            .where(NewsSentiment.ticker == ticker)
            .order_by(NewsSentiment.published_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_fetched_at(self, ticker: str) -> datetime | None:
        """Return the most recent fetched_at for a ticker (TTL check)."""
        stmt = (
            select(NewsSentiment.fetched_at)
            .where(NewsSentiment.ticker == ticker)
            .order_by(NewsSentiment.fetched_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_existing_urls(self, urls: list[str]) -> set[str]:
        """Return URLs that already exist in DB, for deduplication."""
        if not urls:
            return set()
        stmt = select(NewsSentiment.url).where(NewsSentiment.url.in_(urls))
        result = await self.session.execute(stmt)
        return {row[0] for row in result.all()}

    async def bulk_insert(self, rows: list[dict]) -> None:
        """Insert new news rows, skipping any with duplicate URLs."""
        if not rows:
            return
        stmt = insert(NewsSentiment).values(rows)
        stmt = stmt.on_conflict_do_nothing(constraint="uq_news_url")
        await self.session.execute(stmt)
        await self.session.commit()
