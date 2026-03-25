from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.alert import Alert


class AlertRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: int) -> list[Alert]:
        stmt = select(Alert).where(Alert.user_id == user_id, Alert.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(self, user_id: int, ticker: str, **fields) -> Alert:
        stmt = insert(Alert).values(user_id=user_id, ticker=ticker, **fields)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_alert_user_ticker",
            set_={k: getattr(stmt.excluded, k) for k in fields},
        )
        await self.session.execute(stmt)
        await self.session.commit()
        result = await self.session.execute(
            select(Alert).where(Alert.user_id == user_id, Alert.ticker == ticker)
        )
        return result.scalar_one()

    async def delete_by_ticker(self, user_id: int, ticker: str) -> None:
        await self.session.execute(
            delete(Alert).where(Alert.user_id == user_id, Alert.ticker == ticker)
        )
        await self.session.commit()

    async def delete_all(self, user_id: int) -> None:
        await self.session.execute(delete(Alert).where(Alert.user_id == user_id))
        await self.session.commit()
