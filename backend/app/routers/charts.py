from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.services.market_data_service import MarketDataService
from backend.core.scoring import build_chart_data

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/price")
async def get_price_charts(
    tickers: str = Query(..., description="Comma-separated tickers"),
    db: AsyncSession = Depends(get_db),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    mds = MarketDataService(db)

    close_map = {}
    for t in ticker_list:
        try:
            close_map[t] = await mds.get_close_series(t, "3y")
        except Exception:
            pass

    if not close_map:
        return {"price": {}, "drawdown": {}}

    price_df, dd_df = build_chart_data(close_map)

    def _series_to_list(df):
        result = {}
        for col in df.columns:
            result[col] = [
                {"date": dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt),
                 "value": round(float(v), 4)}
                for dt, v in df[col].dropna().items()
            ]
        return result

    return {
        "price": _series_to_list(price_df),
        "drawdown": _series_to_list(dd_df),
    }
