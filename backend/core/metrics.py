from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from backend.core.utils import RISK_FREE_RATE, scale_linear


@dataclass
class PriceMetrics:
    ticker: str
    last: float
    ret_1y: float
    ret_3y: float
    vol_1y: float
    vol_3y: float
    mdd_1y: float
    mdd_3y: float
    sharpe_1y: float
    sharpe_3y: float
    trend_1y: float
    trend_3y: float


@dataclass
class FundamentalMetrics:
    ticker: str
    quote_type: str
    pe: Optional[float]
    pb: Optional[float]
    dividend_yield: Optional[float]
    roe: Optional[float]
    debt_to_equity: Optional[float]
    expense_ratio: Optional[float]
    total_assets: Optional[float]
    score: float


def calc_metrics_for_period(close: pd.Series) -> Dict[str, float]:
    rets = close.pct_change(fill_method=None).dropna()
    total_ret = float(close.iloc[-1] / close.iloc[0] - 1.0) if len(close) > 1 else np.nan
    vol = float(rets.std() * np.sqrt(252)) if len(rets) > 1 else np.nan
    mdd = float(((close / close.cummax()) - 1.0).min()) if len(close) > 1 else np.nan
    if vol and not np.isnan(vol) and vol != 0:
        sharpe = float((rets.mean() * 252 - RISK_FREE_RATE) / vol)
    else:
        sharpe = np.nan

    ma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else np.nan
    ma60 = float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else np.nan
    ma120 = float(close.rolling(120).mean().iloc[-1]) if len(close) >= 120 else np.nan
    last = float(close.iloc[-1])

    trend = 0.0
    if not np.isnan(ma120) and not np.isnan(ma60) and not np.isnan(ma20):
        if last > ma20 and last > ma60 and last > ma120:
            trend = 1.0
        elif last > ma60 and last > ma120:
            trend = 0.66
        elif last > ma20:
            trend = 0.33

    return {
        "last": last,
        "ret": total_ret,
        "vol": vol,
        "mdd": mdd,
        "sharpe": sharpe,
        "trend": trend,
    }


def calculate_price_metrics(
    ticker: str, close_1y: pd.Series, close_3y: pd.Series
) -> PriceMetrics:
    """Calculate price metrics from pre-fetched close series."""
    one_year = calc_metrics_for_period(close_1y)
    three_year = calc_metrics_for_period(close_3y)
    return PriceMetrics(
        ticker=ticker,
        last=one_year["last"],
        ret_1y=one_year["ret"],
        ret_3y=three_year["ret"],
        vol_1y=one_year["vol"],
        vol_3y=three_year["vol"],
        mdd_1y=one_year["mdd"],
        mdd_3y=three_year["mdd"],
        sharpe_1y=one_year["sharpe"],
        sharpe_3y=three_year["sharpe"],
        trend_1y=one_year["trend"],
        trend_3y=three_year["trend"],
    )


def calculate_volume_score(ohlc: pd.DataFrame) -> float:
    """Estimate volume strength score (0-100) from OHLCV."""
    if "Volume" not in ohlc.columns or "Close" not in ohlc.columns:
        return 50.0
    if len(ohlc) < 30:
        return 50.0

    close = ohlc["Close"].astype(float)
    volume = ohlc["Volume"].astype(float).replace(0, np.nan).fillna(method="ffill")
    if volume.isna().all():
        return 50.0

    # 1) Relative volume: today's volume vs. 20-day average.
    avg20 = float(volume.tail(20).mean())
    latest = float(volume.iloc[-1])
    vol_ratio = latest / avg20 if avg20 > 0 else 1.0
    s_ratio = scale_linear(vol_ratio, 0.6, 2.2)

    # 2) OBV trend over the recent window.
    direction = np.sign(close.diff().fillna(0.0))
    obv = (direction * volume).cumsum()
    if len(obv) >= 20:
        obv_trend = float((obv.iloc[-1] - obv.iloc[-20]) / max(abs(obv.iloc[-20]), 1.0))
    else:
        obv_trend = 0.0
    s_obv = scale_linear(obv_trend, -0.3, 0.3)

    # 3) Up-day volume ratio in recent sessions.
    up_mask = close.diff().fillna(0.0) > 0
    recent_volume = volume.tail(20)
    up_volume = float(recent_volume[up_mask.tail(20)].sum())
    total_volume = float(recent_volume.sum())
    up_ratio = up_volume / total_volume if total_volume > 0 else 0.5
    s_up_ratio = scale_linear(up_ratio, 0.35, 0.65)

    return float(0.5 * s_ratio + 0.3 * s_obv + 0.2 * s_up_ratio)
