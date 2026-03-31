"""Yahoo Finance data fetching — pure functions, no Streamlit dependency."""

from functools import lru_cache
from typing import Dict

import pandas as pd
import requests
import yfinance as yf


def fetch_close_series(ticker: str, period: str) -> pd.Series:
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"{ticker} 無法下載到歷史資料")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"].dropna()
    if close.empty:
        raise ValueError(f"{ticker} Close 欄位為空")
    return close


def fetch_ohlc(ticker: str, period: str) -> pd.DataFrame:
    """下載 OHLC 資料，回傳包含 Open/High/Low/Close 的 DataFrame。"""
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"{ticker} 無法下載到歷史資料")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            raise ValueError(f"{ticker} 缺少 {col} 欄位")
    return df[["Open", "High", "Low", "Close"]].dropna()


def fetch_ticker_info(ticker: str) -> Dict:
    return yf.Ticker(ticker).info


@lru_cache(maxsize=1)
def fetch_twse_name_map() -> dict[str, str]:
    """
    Fetch Taiwan listed stock Chinese names from TWSE OpenAPI.
    Returns a mapping {ticker: chinese_name}.
    """
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    rows = resp.json()
    mapping: dict[str, str] = {}
    for row in rows:
        ticker = str(
            row.get("公司代號")
            or row.get("有價證券代號")
            or row.get("股票代號")
            or ""
        ).strip()
        name = str(
            row.get("公司簡稱")
            or row.get("公司名稱")
            or row.get("有價證券名稱")
            or ""
        ).strip()
        if ticker and name:
            mapping[ticker] = name
    return mapping
