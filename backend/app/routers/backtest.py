from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.schemas.backtest import BacktestRequest, BacktestResponse
from backend.app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("", response_model=BacktestResponse)
async def run_backtest(req: BacktestRequest, db: AsyncSession = Depends(get_db)):
    svc = BacktestService(db)
    return await svc.run(req)
