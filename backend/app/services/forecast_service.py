"""3-day forecast service."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.forecast import ForecastResponse
from backend.app.services.market_data_service import MarketDataService
from backend.core.scoring import calc_3day_forecast_from_close


class ForecastService:
    def __init__(self, session: AsyncSession):
        self.mds = MarketDataService(session)

    async def compute_batch(self, tickers: list[str]) -> list[ForecastResponse]:
        results = []
        for t in tickers:
            try:
                close = await self.mds.get_close_series(t, "2y")
                fc = calc_3day_forecast_from_close(close)
                results.append(ForecastResponse(
                    ticker=t,
                    p_up_3d=round(fc["p_up_3d"], 4),
                    p_down_3d=round(fc["p_down_3d"], 4),
                    exp_3d_ret=round(fc["exp_3d_ret"], 6),
                    q10=round(fc["q10"], 6),
                    q50=round(fc["q50"], 6),
                    q90=round(fc["q90"], 6),
                ))
            except Exception:
                pass
        return results
