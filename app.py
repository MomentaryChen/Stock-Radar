import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


RISK_FREE_RATE = 0.015
# 瀏覽器 localStorage 鍵名（與 streamlit-js-eval 搭配）
LOCAL_STORAGE_TICKERS_KEY = "tw_stock_tickers"
DEFAULT_TICKER_TEXT = "2002,2542,00882"


def _ensure_ticker_input_from_local_storage() -> None:
    """首次載入時從 localStorage 還原代號（需 streamlit-js-eval）。"""
    if "ticker_input" in st.session_state:
        return
    try:
        from streamlit_js_eval import streamlit_js_eval
    except ImportError:
        st.session_state["ticker_input"] = DEFAULT_TICKER_TEXT
        return
    stored = streamlit_js_eval(
        js_expressions=f'localStorage.getItem("{LOCAL_STORAGE_TICKERS_KEY}")',
        key="ls_read_tw_stock_tickers",
    )
    st.session_state["ticker_input"] = stored if stored else DEFAULT_TICKER_TEXT


def _save_tickers_to_local_storage(ticker_text: str) -> None:
    try:
        from streamlit_js_eval import streamlit_js_eval
    except ImportError:
        return
    payload = json.dumps(ticker_text)
    streamlit_js_eval(
        js_expressions=f'localStorage.setItem("{LOCAL_STORAGE_TICKERS_KEY}", {payload})',
        key="ls_write_tw_stock_tickers",
    )


def _clear_tickers_local_storage() -> None:
    try:
        from streamlit_js_eval import streamlit_js_eval
    except ImportError:
        return
    streamlit_js_eval(
        js_expressions=f'localStorage.removeItem("{LOCAL_STORAGE_TICKERS_KEY}")',
        key="ls_clear_tw_stock_tickers",
    )
PROFILE_WEIGHTS = {
    "保守": {"fundamental": 0.70, "price": 0.30},
    "平衡": {"fundamental": 0.60, "price": 0.40},
    "積極": {"fundamental": 0.45, "price": 0.55},
}


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


def clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def scale_linear(value: float, low: float, high: float) -> float:
    if math.isclose(high, low):
        return 50.0
    return clamp_0_100((value - low) / (high - low) * 100.0)


def scale_inverse(value: float, low: float, high: float) -> float:
    return 100.0 - scale_linear(value, low, high)


def safe_float(v: object) -> Optional[float]:
    if v is None:
        return None
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(fv):
        return None
    return fv


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


def calc_metrics_for_period(close: pd.Series) -> Dict[str, float]:
    rets = close.pct_change().dropna()
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


def calculate_price_metrics(ticker: str) -> PriceMetrics:
    one_year = calc_metrics_for_period(fetch_close_series(ticker, "1y"))
    three_year = calc_metrics_for_period(fetch_close_series(ticker, "3y"))
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


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ticker_info(ticker: str) -> Dict:
    return yf.Ticker(ticker).info


def normalize_ratio(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    # If APIs return percentage format like 7.1, convert to 0.071.
    if v > 1.0:
        return v / 100.0
    return v


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

    # Price factors score: 1Y + 3Y mixed
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

    # Final score by risk profile
    weight = PROFILE_WEIGHTS[profile]
    df["total_score"] = weight["fundamental"] * df["fundamental"] + weight["price"] * df["price_score"]
    df["recommendation"] = df["total_score"].apply(summarize_recommendation)

    return df.sort_values("total_score", ascending=False).reset_index(drop=True)


def normalize_tickers(raw: str) -> List[str]:
    parts = [x.strip() for x in raw.replace(" ", "").split(",") if x.strip()]
    normalized = []
    for p in parts:
        if p.endswith(".TW"):
            normalized.append(p)
        elif p.isdigit():
            normalized.append(f"{p}.TW")
        else:
            normalized.append(p)
    return normalized


def as_pct(v: Optional[float]) -> str:
    if v is None or np.isnan(v):
        return "-"
    return f"{v * 100:.2f}%"


def as_ratio(v: Optional[float]) -> str:
    if v is None or np.isnan(v):
        return "-"
    return f"{v:.2f}"


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
    returns = close.pct_change().dropna()
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


def main() -> None:
    st.set_page_config(page_title="台股量化評分 UI", layout="wide")
    st.title("台股量化評分與推薦")
    st.caption("精簡主畫面：先看結論，細節可展開查看。資料來源：Yahoo Finance。")

    with st.sidebar:
        st.subheader("輸入設定")
        _ensure_ticker_input_from_local_storage()
        ticker_text = st.text_input(
            "台股代號（逗號分隔）",
            key="ticker_input",
            help="會自動記在瀏覽器 localStorage，下次開啟會還原。",
        )
        profile = st.radio("投資風格", ["保守", "平衡", "積極"], index=1, horizontal=True)
        remember = st.checkbox("計算成功後記住代號到瀏覽器", value=True)
        col_a, col_b = st.columns(2)
        with col_a:
            run = st.button("開始計算", type="primary")
        with col_b:
            if st.button("清除記憶"):
                _clear_tickers_local_storage()
                st.session_state["ticker_input"] = DEFAULT_TICKER_TEXT
                st.rerun()

    if not run:
        st.info("調整完設定後，按「開始計算」。")
        return

    tickers = normalize_tickers(ticker_text)
    if not tickers:
        st.error("請至少輸入一個代號。")
        return

    metrics = []
    fundamentals: Dict[str, FundamentalMetrics] = {}
    chart_close_map: Dict[str, pd.Series] = {}
    forecast_map: Dict[str, Dict[str, float]] = {}
    errors = []
    with st.spinner("下載資料與計算中..."):
        for t in tickers:
            try:
                metrics.append(calculate_price_metrics(t))
                info = fetch_ticker_info(t)
                fundamentals[t] = score_fundamental_from_info(t, info)
                chart_close_map[t] = fetch_close_series(t, "3y")
                forecast_map[t] = calc_3day_forecast_from_close(fetch_close_series(t, "2y"))
            except Exception as exc:  # pylint: disable=broad-except
                errors.append(f"{t}: {exc}")

    if errors:
        st.warning("部分代號無法計算：")
        for e in errors:
            st.write(f"- {e}")

    if not metrics:
        st.error("沒有可用結果。請確認代號格式（例如 2330, 0050, 00882）。")
        return

    if remember:
        _save_tickers_to_local_storage(ticker_text.strip())

    scored = build_scores(metrics, fundamentals, profile)

    display_cols = [
        "ticker",
        "last",
        "total_score",
        "recommendation",
    ]
    detail_cols = [
        "ticker",
        "fundamental",
        "price_score",
        "ret_1y",
        "ret_3y",
        "vol_1y",
        "vol_3y",
        "mdd_1y",
        "mdd_3y",
        "sharpe_1y",
        "sharpe_3y",
    ]
    summary_view = scored[display_cols].copy()
    detail_view = scored[detail_cols].copy()
    pct_cols = ["ret_1y", "ret_3y", "vol_1y", "vol_3y", "mdd_1y", "mdd_3y"]
    for c in pct_cols:
        detail_view[c] = detail_view[c].apply(as_pct)
    summary_view["last"] = summary_view["last"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    summary_view["total_score"] = summary_view["total_score"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    for c in ["fundamental", "price_score", "sharpe_1y", "sharpe_3y"]:
        detail_view[c] = detail_view[c].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

    top = scored.iloc[0]

    tabs = st.tabs(["總覽", "預測", "圖表", "進階資料"])

    with tabs[0]:
        st.subheader("量化排名（精簡）")
        st.dataframe(summary_view, use_container_width=True, hide_index=True)
        st.success(
            f"目前第一名：{top['ticker']} | 總分 {top['total_score']:.1f} | {top['recommendation']}"
        )

    with tabs[1]:
        st.subheader("3天機率預測")
        forecast_rows = []
        for t in scored["ticker"].tolist():
            f3 = forecast_map.get(t)
            if not f3:
                forecast_rows.append(
                    {
                        "ticker": t,
                        "p_up_3d": "-",
                        "p_down_3d": "-",
                        "exp_3d_ret": "-",
                        "range_10_90": "資料不足",
                    }
                )
                continue
            forecast_rows.append(
                {
                    "ticker": t,
                    "p_up_3d": as_pct(f3["p_up_3d"]),
                    "p_down_3d": as_pct(f3["p_down_3d"]),
                    "exp_3d_ret": as_pct(f3["exp_3d_ret"]),
                    "range_10_90": f"{as_pct(f3['q10'])} ~ {as_pct(f3['q90'])}",
                }
            )
        st.dataframe(pd.DataFrame(forecast_rows), use_container_width=True, hide_index=True)
        st.caption("此預測是統計機率模型，非保證結果。")

    with tabs[2]:
        st.subheader("圖表：3年價格、回撤、分數")
        if not chart_close_map:
            st.warning("目前無可用圖表資料。")
        else:
            price_df, drawdown_df = build_chart_data(chart_close_map)
            st.caption("價格圖採 3 年期、起點標準化為 100。")
            st.line_chart(price_df, use_container_width=True)
            st.caption("回撤圖（%）：越接近 0 代表距離歷史高點越近。")
            st.line_chart(drawdown_df, use_container_width=True)
            comp = scored[["ticker", "fundamental", "price_score", "total_score"]].copy()
            comp = comp.set_index("ticker")
            st.bar_chart(comp, use_container_width=True)

    with tabs[3]:
        st.subheader("完整量化指標")
        st.dataframe(detail_view, use_container_width=True, hide_index=True)
        f_rows = []
        for t in scored["ticker"].tolist():
            f = fundamentals.get(t)
            if not f:
                continue
            f_rows.append(
                {
                    "ticker": t,
                    "type": f.quote_type,
                    "pe": as_ratio(f.pe),
                    "pb": as_ratio(f.pb),
                    "dividend_yield": as_pct(f.dividend_yield),
                    "roe": as_pct(f.roe),
                    "debt_to_equity": as_ratio(f.debt_to_equity),
                    "expense_ratio": as_pct(f.expense_ratio),
                    "fundamental_score": f"{f.score:.2f}",
                }
            )
        st.subheader("基本面自動抓取")
        if f_rows:
            st.dataframe(pd.DataFrame(f_rows), use_container_width=True, hide_index=True)
        st.subheader("模型說明")
        st.markdown(
            """
            - 基本面分自動由 yfinance 指標估算（股票與 ETF 權重不同）
            - 總分依風格切換：保守/平衡/積極
            - 歷史股價因子包含：1Y/3Y 報酬、波動、最大回撤、Sharpe、均線趨勢
            - 3天預測為統計機率模型（非保證），僅供決策輔助
            - 這是決策輔助工具，不是投資建議
            """
        )


if __name__ == "__main__":
    main()
