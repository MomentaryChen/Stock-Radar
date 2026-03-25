from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.repositories.alert_repo import AlertRepo
from backend.app.schemas.alert import AlertResponse, AlertUpsert

router = APIRouter(prefix="/alerts", tags=["alerts"])

DEFAULT_USER_ID = 1


@router.get("", response_model=list[AlertResponse])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    repo = AlertRepo(db)
    return await repo.get_all(DEFAULT_USER_ID)


@router.put("/{ticker}", response_model=AlertResponse)
async def upsert_alert(ticker: str, body: AlertUpsert, db: AsyncSession = Depends(get_db)):
    repo = AlertRepo(db)
    alert = await repo.upsert(
        DEFAULT_USER_ID,
        ticker,
        score_above=body.score_above,
        score_below=body.score_below,
        price_above=body.price_above,
        price_below=body.price_below,
        rsi_overbought=body.rsi_overbought,
        rsi_oversold=body.rsi_oversold,
    )
    return alert


@router.delete("/{ticker}", status_code=204)
async def delete_alert(ticker: str, db: AsyncSession = Depends(get_db)):
    repo = AlertRepo(db)
    await repo.delete_by_ticker(DEFAULT_USER_ID, ticker)


@router.delete("", status_code=204)
async def clear_all_alerts(db: AsyncSession = Depends(get_db)):
    repo = AlertRepo(db)
    await repo.delete_all(DEFAULT_USER_ID)
