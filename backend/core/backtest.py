"""Backtest engine with configurable strategy and rebalance rules."""

from dataclasses import dataclass
from typing import Dict, Literal

import numpy as np
import pandas as pd

from backend.core.utils import RISK_FREE_RATE


@dataclass
class BacktestResult:
    """Backtest result summary."""
    cumulative_return: float
    annualized_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    annualized_volatility: float
    total_rebalances: int
    average_turnover: float
    monthly_returns: pd.Series
    equity_curve: pd.Series
    benchmark_curve: pd.Series


def _pick_rebalance_dates(
    index: pd.DatetimeIndex, rebalance: Literal["monthly", "weekly"]
) -> list[pd.Timestamp]:
    if rebalance == "weekly":
        grouped = pd.Series(index=index, data=1).groupby(index.to_period("W-FRI"))
    else:
        grouped = pd.Series(index=index, data=1).groupby(index.to_period("M"))
    return [group.index[0] for _, group in grouped]


def _normalize_weights(raw: pd.Series) -> pd.Series:
    total = float(raw.sum())
    if total <= 0:
        return raw * 0
    return raw / total


def _build_target_weights(
    prices_until_now: pd.DataFrame,
    strategy: Literal["equal_weight", "top_n_momentum"],
    top_n: int,
    lookback_days: int,
) -> pd.Series:
    latest = prices_until_now.iloc[-1]
    available = latest.dropna().index
    if len(available) == 0:
        return pd.Series(index=prices_until_now.columns, data=0.0)

    if strategy == "equal_weight":
        selected = list(available)
    else:
        if len(prices_until_now) <= lookback_days:
            selected = list(available)[:top_n]
        else:
            momentum = prices_until_now.iloc[-1] / prices_until_now.iloc[-lookback_days] - 1
            momentum = momentum.dropna().sort_values(ascending=False)
            selected = list(momentum.head(top_n).index) if not momentum.empty else list(available)[:top_n]

    weights = pd.Series(index=prices_until_now.columns, data=0.0)
    if selected:
        weights.loc[selected] = 1.0
    return _normalize_weights(weights)


def run_backtest(
    ticker_close_map: Dict[str, pd.Series],
    benchmark_close: pd.Series,
    months: int = 12,
    strategy: Literal["equal_weight", "top_n_momentum"] = "equal_weight",
    rebalance: Literal["monthly", "weekly"] = "monthly",
    top_n: int = 3,
    lookback_days: int = 60,
    transaction_cost_bps: float = 10.0,
) -> BacktestResult:
    """Simulate a portfolio against benchmark with configurable settings."""
    if not ticker_close_map:
        raise ValueError("No available stock data for backtest")

    all_close = pd.DataFrame(ticker_close_map)
    all_close = all_close.dropna(how="all")

    if len(all_close) < 60:
        raise ValueError("Not enough history, at least 60 trading days required")

    end_date = all_close.index[-1]
    start_date = end_date - pd.DateOffset(months=months)
    all_close = all_close.loc[all_close.index >= start_date]
    all_close = all_close.ffill().dropna(how="all")

    daily_returns = all_close.pct_change(fill_method=None)
    daily_returns = daily_returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")

    if len(daily_returns) < 20:
        raise ValueError("Insufficient trading days in backtest period")

    rebal_dates = set(_pick_rebalance_dates(daily_returns.index, rebalance))
    current_weights = pd.Series(index=daily_returns.columns, data=0.0)
    strategy_returns: list[float] = []
    turnovers: list[float] = []

    for dt in daily_returns.index:
        cost = 0.0
        if dt in rebal_dates:
            prices_until_now = all_close.loc[all_close.index <= dt]
            target_weights = _build_target_weights(
                prices_until_now=prices_until_now,
                strategy=strategy,
                top_n=top_n,
                lookback_days=lookback_days,
            )
            turnover = float((target_weights - current_weights).abs().sum())
            turnovers.append(turnover)
            current_weights = target_weights
            cost = turnover * (transaction_cost_bps / 10000.0)

        ret_vec = daily_returns.loc[dt].fillna(0.0)
        day_ret = float((current_weights * ret_vec).sum() - cost)
        strategy_returns.append(day_ret)

    strategy_daily = pd.Series(strategy_returns, index=daily_returns.index, dtype=float)

    bench_ret = benchmark_close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).dropna()
    bench_ret = bench_ret.reindex(strategy_daily.index).fillna(0.0)

    equity = (1 + strategy_daily).cumprod()
    bench_equity = (1 + bench_ret).cumprod()

    monthly = strategy_daily.resample("ME").apply(lambda x: (1 + x).prod() - 1)

    cum_ret = float(equity.iloc[-1] - 1)
    n_years = len(strategy_daily) / 252
    ann_ret = float((1 + cum_ret) ** (1 / n_years) - 1) if n_years > 0 else 0.0
    mdd = float(((equity / equity.cummax()) - 1).min())
    vol = float(strategy_daily.std() * np.sqrt(252))
    sharpe = float((strategy_daily.mean() * 252 - RISK_FREE_RATE) / vol) if vol > 0 else 0.0
    win_rate = float((monthly > 0).sum() / len(monthly)) if len(monthly) > 0 else 0.0

    return BacktestResult(
        cumulative_return=cum_ret,
        annualized_return=ann_ret,
        max_drawdown=mdd,
        sharpe=sharpe,
        win_rate=win_rate,
        annualized_volatility=vol,
        total_rebalances=len(turnovers),
        average_turnover=float(np.mean(turnovers)) if turnovers else 0.0,
        monthly_returns=monthly,
        equity_curve=equity,
        benchmark_curve=bench_equity,
    )
