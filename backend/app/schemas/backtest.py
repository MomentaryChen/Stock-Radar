from pydantic import BaseModel


class BacktestRequest(BaseModel):
    tickers: list[str]
    months: int = 12


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
    monthly_returns: list[MonthlyReturn]
    equity_curve: list[TimeSeriesPoint]
    benchmark_curve: list[TimeSeriesPoint]
