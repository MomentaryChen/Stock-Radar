"""Technical indicator service."""

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.technical import (
    TechnicalChartPoint,
    TechnicalChartResponse,
    TechnicalSignalResponse,
)
from backend.app.services.market_data_service import MarketDataService
from backend.core.technical import (
    calc_kd,
    calc_macd,
    calc_rsi,
    compute_technical_signals,
)


class TechnicalService:
    def __init__(self, session: AsyncSession):
        self.mds = MarketDataService(session)

    async def get_signals_batch(self, tickers: list[str]) -> list[TechnicalSignalResponse]:
        results = []
        for t in tickers:
            try:
                ohlc = await self.mds.get_ohlc(t, "1y")
                ts = compute_technical_signals(t, ohlc)
                results.append(TechnicalSignalResponse(
                    ticker=ts.ticker,
                    rsi=round(ts.rsi, 2),
                    rsi_signal=ts.rsi_signal,
                    macd=round(ts.macd, 4),
                    macd_signal=ts.macd_signal,
                    k=round(ts.k, 2),
                    d=round(ts.d, 2),
                    kd_signal=ts.kd_signal,
                ))
            except Exception:
                pass
        return results

    async def get_chart_data(self, ticker: str, period: str = "1y") -> TechnicalChartResponse:
        ohlc = await self.mds.get_ohlc(ticker, period)
        close = ohlc["Close"]
        high = ohlc["High"]
        low = ohlc["Low"]

        rsi_s = calc_rsi(close).dropna()
        macd_df = calc_macd(close).dropna()
        kd_df = calc_kd(high, low, close).dropna()

        def _fmt_date(idx):
            return idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)

        rsi_series = [
            TechnicalChartPoint(date=_fmt_date(dt), value=round(float(v), 2))
            for dt, v in rsi_s.items()
        ]
        macd_series = [
            {
                "date": _fmt_date(dt),
                "macd": round(float(row["MACD"]), 4),
                "signal": round(float(row["Signal"]), 4),
                "histogram": round(float(row["Histogram"]), 4),
            }
            for dt, row in macd_df.iterrows()
        ]
        kd_series = [
            {
                "date": _fmt_date(dt),
                "k": round(float(row["K"]), 2),
                "d": round(float(row["D"]), 2),
            }
            for dt, row in kd_df.iterrows()
        ]

        return TechnicalChartResponse(
            ticker=ticker,
            rsi_series=rsi_series,
            macd_series=macd_series,
            kd_series=kd_series,
        )
