from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.core.metrics import FundamentalMetrics, PriceMetrics
from backend.core.utils import (
    normalize_ratio,
    safe_float,
    scale_inverse,
    scale_linear,
)

PROFILE_WEIGHTS = {
    "保守": {"fundamental": 0.70, "price": 0.30},
    "平衡": {"fundamental": 0.60, "price": 0.40},
    "積極": {"fundamental": 0.45, "price": 0.55},
    "conservative": {"fundamental": 0.70, "price": 0.30},
    "balanced": {"fundamental": 0.60, "price": 0.40},
    "aggressive": {"fundamental": 0.45, "price": 0.55},
}


def score_fundamental_from_info(ticker: str, info: Dict) -> FundamentalMetrics:
    quote_type = str(info.get("quoteType", "EQUITY")).upper()

    pe = safe_float(info.get("trailingPE"))
    pb = safe_float(info.get("priceToBook"))
    dividend_yield = normalize_ratio(safe_float(info.get("dividendYield")))
    roe = normalize_ratio(safe_float(info.get("returnOnEquity")))
    debt_to_equity = safe_float(info.get("debtToEquity"))
    expense_ratio = normalize_ratio(safe_float(info.get("annualReportExpenseRatio")))
    if expense_ratio is None:
        expense_ratio = normalize_ratio(safe_float(info.get("totalExpenseRatio")))
    total_assets = safe_float(info.get("totalAssets"))

    if quote_type == "ETF":
        score_items = [
            (scale_linear(dividend_yield if dividend_yield is not None else 0.04, 0.0, 0.10), 0.45),
            (scale_inverse(expense_ratio if expense_ratio is not None else 0.008, 0.0, 0.015), 0.30),
            (scale_linear(total_assets if total_assets is not None else 1e10, 1e9, 2e11), 0.25),
        ]
    else:
        score_items = [
            (scale_inverse(pe if pe is not None else 18.0, 8.0, 30.0), 0.20),
            (scale_inverse(pb if pb is not None else 1.5, 0.7, 3.0), 0.20),
            (scale_linear(dividend_yield if dividend_yield is not None else 0.03, 0.0, 0.10), 0.20),
            (scale_linear(roe if roe is not None else 0.08, -0.05, 0.25), 0.20),
            (scale_inverse(debt_to_equity if debt_to_equity is not None else 120.0, 20.0, 280.0), 0.20),
        ]

    score = float(sum(v * w for v, w in score_items))
    return FundamentalMetrics(
        ticker=ticker,
        quote_type=quote_type,
        pe=pe,
        pb=pb,
        dividend_yield=dividend_yield,
        roe=roe,
        debt_to_equity=debt_to_equity,
        expense_ratio=expense_ratio,
        total_assets=total_assets,
        score=score,
    )


def summarize_recommendation(total_score: float) -> str:
    if total_score >= 65:
        return "推薦（可作核心或優先配置）"
    if total_score >= 55:
        return "中立（可小部位）"
    return "保守觀望（暫不主動加碼）"


def build_scores(
    metrics_list: List[PriceMetrics],
    fundamentals: Dict[str, FundamentalMetrics],
    profile: str,
) -> pd.DataFrame:
    rows = []
    for m in metrics_list:
        rows.append(
            {
                "ticker": m.ticker,
                "last": m.last,
                "ret_1y": m.ret_1y,
                "ret_3y": m.ret_3y,
                "vol_1y": m.vol_1y,
                "vol_3y": m.vol_3y,
                "mdd_1y": m.mdd_1y,
                "mdd_3y": m.mdd_3y,
                "sharpe_1y": m.sharpe_1y,
                "sharpe_3y": m.sharpe_3y,
                "trend_1y": m.trend_1y,
                "trend_3y": m.trend_3y,
                "fundamental": fundamentals[m.ticker].score if m.ticker in fundamentals else 55.0,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["s_ret_1y"] = df["ret_1y"].apply(lambda v: scale_linear(v, -0.3, 0.5))
    df["s_ret_3y"] = df["ret_3y"].apply(lambda v: scale_linear(v, -0.5, 1.0))
    df["s_vol_1y"] = df["vol_1y"].apply(lambda v: scale_inverse(v, 0.12, 0.40))
    df["s_vol_3y"] = df["vol_3y"].apply(lambda v: scale_inverse(v, 0.12, 0.40))
    df["s_mdd_1y"] = df["mdd_1y"].apply(lambda v: scale_linear(v, -0.5, -0.05))
    df["s_mdd_3y"] = df["mdd_3y"].apply(lambda v: scale_linear(v, -0.6, -0.10))
    df["s_sharpe_1y"] = df["sharpe_1y"].apply(lambda v: scale_linear(v, -1.0, 1.5))
    df["s_sharpe_3y"] = df["sharpe_3y"].apply(lambda v: scale_linear(v, -1.0, 1.5))
    df["s_trend_1y"] = df["trend_1y"] * 100.0
    df["s_trend_3y"] = df["trend_3y"] * 100.0

    df["price_score"] = (
        0.15 * df["s_ret_1y"]
        + 0.25 * df["s_ret_3y"]
        + 0.07 * df["s_vol_1y"]
        + 0.08 * df["s_vol_3y"]
        + 0.08 * df["s_mdd_1y"]
        + 0.12 * df["s_mdd_3y"]
        + 0.07 * df["s_sharpe_1y"]
        + 0.12 * df["s_sharpe_3y"]
        + 0.03 * df["s_trend_1y"]
        + 0.03 * df["s_trend_3y"]
    )

    weight = PROFILE_WEIGHTS[profile]
    df["total_score"] = weight["fundamental"] * df["fundamental"] + weight["price"] * df["price_score"]
    df["recommendation"] = df["total_score"].apply(summarize_recommendation)

    return df.sort_values("total_score", ascending=False).reset_index(drop=True)


def build_chart_data(
    ticker_close_map: Dict[str, pd.Series],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    price_df = pd.DataFrame()
    drawdown_df = pd.DataFrame()
    for ticker, close in ticker_close_map.items():
        norm = close / close.iloc[0] * 100.0
        dd = (close / close.cummax() - 1.0) * 100.0
        price_df[ticker] = norm
        drawdown_df[ticker] = dd
    return price_df, drawdown_df


def calc_3day_forecast_from_close(close: pd.Series) -> Dict[str, float]:
    returns = close.pct_change(fill_method=None).dropna()
    if len(returns) < 80:
        raise ValueError("歷史資料不足，無法估計3天機率")

    mom5 = float(close.iloc[-1] / close.iloc[-6] - 1.0) if len(close) >= 6 else 0.0
    mu = float(returns.tail(60).mean()) + 0.15 * (mom5 / 5.0)
    sigma = float(returns.tail(60).std())
    if sigma <= 0 or np.isnan(sigma):
        raise ValueError("波動為0或資料異常，無法估計3天機率")

    sims = np.random.normal(mu, sigma, (20000, 3))
    path_ret = (1.0 + sims).prod(axis=1) - 1.0
    q10, q50, q90 = np.quantile(path_ret, [0.1, 0.5, 0.9])
    return {
        "p_up_3d": float((path_ret > 0).mean()),
        "p_down_3d": float((path_ret < 0).mean()),
        "exp_3d_ret": float(path_ret.mean()),
        "q10": float(q10),
        "q50": float(q50),
        "q90": float(q90),
    }
