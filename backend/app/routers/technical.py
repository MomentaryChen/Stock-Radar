from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.schemas.technical import TechnicalChartResponse, TechnicalSignalResponse
from backend.app.services.technical_service import TechnicalService

router = APIRouter(prefix="/technical", tags=["technical"])


class BatchRequest(BaseModel):
    tickers: list[str]


@router.post("/batch", response_model=list[TechnicalSignalResponse])
async def batch_signals(req: BatchRequest, db: AsyncSession = Depends(get_db)):
    svc = TechnicalService(db)
    return await svc.get_signals_batch(req.tickers)


@router.get("/{ticker}", response_model=TechnicalChartResponse)
async def get_chart(ticker: str, period: str = "1y", db: AsyncSession = Depends(get_db)):
    svc = TechnicalService(db)
    return await svc.get_chart_data(ticker, period)
