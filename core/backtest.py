"""簡易回測引擎：根據評分模型，每月重新評分並模擬等權買入推薦股。"""

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from core.utils import RISK_FREE_RATE


@dataclass
class BacktestResult:
    """回測結果摘要。"""
    cumulative_return: float
    annualized_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    monthly_returns: pd.Series
    equity_curve: pd.Series
    benchmark_curve: pd.Series


def run_backtest(
    ticker_close_map: Dict[str, pd.Series],
    benchmark_close: pd.Series,
    months: int = 12,
) -> BacktestResult:
    """
    以等權配置所有輸入股票，每月再平衡，對比大盤(benchmark)。

    Args:
        ticker_close_map: 各股票的 Close 序列（至少需涵蓋回測期間）
        benchmark_close: 大盤基準 Close 序列
        months: 回測月數
    """
    if not ticker_close_map:
        raise ValueError("沒有可用的股票資料進行回測")

    # 建立統一日期範圍的收盤價 DataFrame
    all_close = pd.DataFrame(ticker_close_map)
    all_close = all_close.dropna(how="all")

    if len(all_close) < 60:
        raise ValueError("歷史資料不足，需至少 60 個交易日")

    # 計算每日報酬
    daily_returns = all_close.pct_change(fill_method=None).dropna()

    # 截取最近 N 個月
    end_date = daily_returns.index[-1]
    start_date = end_date - pd.DateOffset(months=months)
    daily_returns = daily_returns.loc[daily_returns.index >= start_date]

    if len(daily_returns) < 20:
        raise ValueError("回測期間內交易日不足")

    # 等權配置策略報酬
    n_stocks = daily_returns.shape[1]
    strategy_daily = daily_returns.mean(axis=1)  # 等權 = 平均

    # 大盤基準
    bench_ret = benchmark_close.pct_change(fill_method=None).dropna()
    bench_ret = bench_ret.reindex(strategy_daily.index).fillna(0)

    # 累積淨值
    equity = (1 + strategy_daily).cumprod()
    bench_equity = (1 + bench_ret).cumprod()

    # 月度報酬
    monthly = strategy_daily.resample("ME").apply(lambda x: (1 + x).prod() - 1)

    # 績效指標
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
        monthly_returns=monthly,
        equity_curve=equity,
        benchmark_curve=bench_equity,
    )
