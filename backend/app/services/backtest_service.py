"""Backtest service."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.schemas.backtest import (
    BacktestResponse,
    MonthlyReturn,
    TimeSeriesPoint,
)
from backend.app.services.market_data_service import MarketDataService
from backend.core.backtest import run_backtest


class BacktestService:
    def __init__(self, session: AsyncSession):
        self.mds = MarketDataService(session)

    async def run(self, tickers: list[str], months: int = 12) -> BacktestResponse:
        ticker_close_map = {}
        for t in tickers:
            close = await self.mds.get_close_series(t, "3y")
            ticker_close_map[t] = close

        bench_close = await self.mds.get_close_series(settings.default_benchmark, "3y")
        bt = run_backtest(ticker_close_map, bench_close, months=months)

        def _fmt(idx):
            return idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)

        monthly = [
            MonthlyReturn(month=_fmt(dt), ret=round(float(v), 6))
            for dt, v in bt.monthly_returns.items()
        ]
        equity = [
            TimeSeriesPoint(date=_fmt(dt), value=round(float(v), 6))
            for dt, v in bt.equity_curve.items()
        ]
        benchmark = [
            TimeSeriesPoint(date=_fmt(dt), value=round(float(v), 6))
            for dt, v in bt.benchmark_curve.items()
        ]

        return BacktestResponse(
            cumulative_return=round(bt.cumulative_return, 6),
            annualized_return=round(bt.annualized_return, 6),
            max_drawdown=round(bt.max_drawdown, 6),
            sharpe=round(bt.sharpe, 4),
            win_rate=round(bt.win_rate, 4),
            monthly_returns=monthly,
            equity_curve=equity,
            benchmark_curve=benchmark,
        )
