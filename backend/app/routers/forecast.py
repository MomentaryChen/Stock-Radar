from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.schemas.forecast import ForecastResponse
from backend.app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["forecast"])


class BatchRequest(BaseModel):
    tickers: list[str]


@router.post("/batch", response_model=list[ForecastResponse])
async def batch_forecast(req: BatchRequest, db: AsyncSession = Depends(get_db)):
    svc = ForecastService(db)
    return await svc.compute_batch(req.tickers)
