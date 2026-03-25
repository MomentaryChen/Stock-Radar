from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.industry import Industry


class IndustryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Industry]:
        result = await self.session.execute(select(Industry).order_by(Industry.id))
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Industry | None:
        result = await self.session.execute(select(Industry).where(Industry.name == name))
        return result.scalar_one_or_none()
