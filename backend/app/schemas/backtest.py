from typing import Literal

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    tickers: list[str]
    months: int = 12
    strategy: Literal["equal_weight", "top_n_momentum"] = "equal_weight"
    rebalance: Literal["monthly", "weekly"] = "monthly"
    top_n: int = Field(default=3, ge=1, le=20)
    lookback_days: int = Field(default=60, ge=20, le=252)
    transaction_cost_bps: float = Field(default=10.0, ge=0.0, le=200.0)


class MonthlyReturn(BaseModel):
    month: str
    ret: float


class TimeSeriesPoint(BaseModel):
    date: str
    value: float


class BacktestResponse(BaseModel):
    cumulative_return: float
    annualized_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    annualized_volatility: float
    total_rebalances: int
    average_turnover: float
    monthly_returns: list[MonthlyReturn]
    equity_curve: list[TimeSeriesPoint]
    benchmark_curve: list[TimeSeriesPoint]
