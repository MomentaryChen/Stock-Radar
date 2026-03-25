from typing import Dict

import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=1800, show_spinner=False)
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


@st.cache_data(ttl=1800, show_spinner=False)
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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ticker_info(ticker: str) -> Dict:
    return yf.Ticker(ticker).info
