"""技術指標計算：RSI、MACD、KD。"""

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class TechnicalSignals:
    """某檔股票的技術指標快照。"""
    ticker: str
    rsi: float
    rsi_signal: str
    macd: float
    macd_signal_line: float
    macd_histogram: float
    macd_signal: str
    k: float
    d: float
    kd_signal: str


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def calc_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "MACD": macd_line,
        "Signal": signal_line,
        "Histogram": histogram,
    })


def calc_kd(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 9,
    d_period: int = 3,
) -> pd.DataFrame:
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan) * 100.0
    k = rsv.ewm(com=d_period - 1, min_periods=1).mean()
    d = k.ewm(com=d_period - 1, min_periods=1).mean()
    return pd.DataFrame({"K": k, "D": d})


def _rsi_signal(rsi: float) -> str:
    if rsi >= 80:
        return "嚴重超買"
    if rsi >= 70:
        return "超買"
    if rsi <= 20:
        return "嚴重超賣"
    if rsi <= 30:
        return "超賣"
    return "中性"


def _macd_signal(macd: float, signal: float, hist: float, prev_hist: float) -> str:
    if hist > 0 and prev_hist <= 0:
        return "黃金交叉"
    if hist < 0 and prev_hist >= 0:
        return "死亡交叉"
    if hist > 0:
        return "多頭"
    return "空頭"


def _kd_signal(k: float, d: float, prev_k: float, prev_d: float) -> str:
    if k > d and prev_k <= prev_d:
        return "黃金交叉"
    if k < d and prev_k >= prev_d:
        return "死亡交叉"
    if k >= 80 and d >= 80:
        return "超買區"
    if k <= 20 and d <= 20:
        return "超賣區"
    if k > d:
        return "多頭排列"
    return "空頭排列"


def compute_technical_signals(
    ticker: str, ohlc: pd.DataFrame
) -> TechnicalSignals:
    """從 OHLC DataFrame 計算所有技術指標並回傳快照。"""
    close = ohlc["Close"]
    high = ohlc["High"]
    low = ohlc["Low"]

    rsi_series = calc_rsi(close)
    macd_df = calc_macd(close)
    kd_df = calc_kd(high, low, close)

    rsi_val = float(rsi_series.iloc[-1])
    macd_val = float(macd_df["MACD"].iloc[-1])
    signal_val = float(macd_df["Signal"].iloc[-1])
    hist_val = float(macd_df["Histogram"].iloc[-1])
    prev_hist = float(macd_df["Histogram"].iloc[-2]) if len(macd_df) >= 2 else 0.0
    k_val = float(kd_df["K"].iloc[-1])
    d_val = float(kd_df["D"].iloc[-1])
    prev_k = float(kd_df["K"].iloc[-2]) if len(kd_df) >= 2 else k_val
    prev_d = float(kd_df["D"].iloc[-2]) if len(kd_df) >= 2 else d_val

    return TechnicalSignals(
        ticker=ticker,
        rsi=rsi_val,
        rsi_signal=_rsi_signal(rsi_val),
        macd=macd_val,
        macd_signal_line=signal_val,
        macd_histogram=hist_val,
        macd_signal=_macd_signal(macd_val, signal_val, hist_val, prev_hist),
        k=k_val,
        d=d_val,
        kd_signal=_kd_signal(k_val, d_val, prev_k, prev_d),
    )
