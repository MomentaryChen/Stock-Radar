from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.watchlist import Watchlist


class WatchlistRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, user_id: int) -> list[Watchlist]:
        result = await self.session.execute(
            select(Watchlist).where(Watchlist.user_id == user_id).order_by(Watchlist.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, watchlist_id: int) -> Watchlist | None:
        return await self.session.get(Watchlist, watchlist_id)

    async def create(self, user_id: int, name: str, tickers: list[str]) -> Watchlist:
        wl = Watchlist(user_id=user_id, name=name, tickers=tickers)
        self.session.add(wl)
        await self.session.commit()
        await self.session.refresh(wl)
        return wl

    async def update(self, wl: Watchlist, **fields) -> Watchlist:
        for k, v in fields.items():
            if v is not None:
                setattr(wl, k, v)
        await self.session.commit()
        await self.session.refresh(wl)
        return wl

    async def delete(self, wl: Watchlist) -> None:
        await self.session.delete(wl)
        await self.session.commit()
