"""Backtest service."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.schemas.backtest import (
    BacktestResponse,
    BacktestRequest,
    MonthlyReturn,
    TimeSeriesPoint,
)
from backend.app.services.market_data_service import MarketDataService
from backend.core.backtest import run_backtest


class BacktestService:
    def __init__(self, session: AsyncSession):
        self.mds = MarketDataService(session)

    async def run(self, req: BacktestRequest) -> BacktestResponse:
        ticker_close_map = {}
        for t in req.tickers:
            close = await self.mds.get_close_series(t, "3y")
            ticker_close_map[t] = close

        bench_close = await self.mds.get_close_series(settings.default_benchmark, "3y")
        bt = run_backtest(
            ticker_close_map,
            bench_close,
            months=req.months,
            strategy=req.strategy,
            rebalance=req.rebalance,
            top_n=req.top_n,
            lookback_days=req.lookback_days,
            transaction_cost_bps=req.transaction_cost_bps,
        )

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
            annualized_volatility=round(bt.annualized_volatility, 6),
            total_rebalances=bt.total_rebalances,
            average_turnover=round(bt.average_turnover, 6),
            monthly_returns=monthly,
            equity_curve=equity,
            benchmark_curve=benchmark,
        )
