from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.repositories.industry_repo import IndustryRepo

router = APIRouter(prefix="/industries", tags=["industries"])


@router.get("")
async def list_industries(db: AsyncSession = Depends(get_db)):
    repo = IndustryRepo(db)
    industries = await repo.get_all()
    return [{"name": i.name, "tickers": i.tickers} for i in industries]
