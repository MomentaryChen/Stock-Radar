import json
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st

from core.data import fetch_close_series, fetch_ohlc, fetch_ticker_info
from core.metrics import FundamentalMetrics, PriceMetrics, calculate_price_metrics
from core.scoring import (
    build_chart_data,
    build_scores,
    calc_3day_forecast_from_close,
    score_fundamental_from_info,
)
from core.technical import (
    TechnicalSignals,
    calc_kd,
    calc_macd,
    calc_rsi,
    compute_technical_signals,
)
from core.backtest import run_backtest
from core.utils import as_pct, as_ratio

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LOCAL_STORAGE_TICKERS_KEY = "tw_stock_tickers"
LOCAL_STORAGE_WATCHLISTS_KEY = "tw_stock_watchlists"
LOCAL_STORAGE_SCORE_HISTORY_KEY = "tw_stock_score_history"
LOCAL_STORAGE_ALERTS_KEY = "tw_stock_alerts"
DEFAULT_TICKER_TEXT = "2002,2542,00882"

INDUSTRY_MAP = {
    "半導體": ["2330.TW", "2303.TW", "2454.TW", "3711.TW"],
    "金融": ["2881.TW", "2882.TW", "2884.TW", "2886.TW"],
    "傳產": ["1301.TW", "1303.TW", "2002.TW", "1326.TW"],
    "電子零組件": ["2317.TW", "2382.TW", "3008.TW"],
    "ETF": ["0050.TW", "0056.TW", "00878.TW", "00882.TW"],
}

# ---------------------------------------------------------------------------
# localStorage helpers
# ---------------------------------------------------------------------------

def _js_eval(js: str, key: str):
    try:
        from streamlit_js_eval import streamlit_js_eval
    except ImportError:
        return None
    return streamlit_js_eval(js_expressions=js, key=key)


def _ensure_ticker_input_from_local_storage() -> None:
    if "ticker_input" in st.session_state:
        return
    stored = _js_eval(
        f'localStorage.getItem("{LOCAL_STORAGE_TICKERS_KEY}")',
        "ls_read_tw_stock_tickers",
    )
    st.session_state["ticker_input"] = stored if stored else DEFAULT_TICKER_TEXT


def _save_tickers_to_local_storage(ticker_text: str) -> None:
    payload = json.dumps(ticker_text)
    _js_eval(
        f'localStorage.setItem("{LOCAL_STORAGE_TICKERS_KEY}", {payload})',
        "ls_write_tw_stock_tickers",
    )


def _clear_tickers_local_storage() -> None:
    _js_eval(
        f'localStorage.removeItem("{LOCAL_STORAGE_TICKERS_KEY}")',
        "ls_clear_tw_stock_tickers",
    )


# ---------------------------------------------------------------------------
# Watchlist helpers (localStorage JSON)
# ---------------------------------------------------------------------------

def _load_watchlists() -> Dict[str, List[str]]:
    raw = _js_eval(
        f'localStorage.getItem("{LOCAL_STORAGE_WATCHLISTS_KEY}")',
        "ls_read_watchlists",
    )
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {"核心持股": [], "觀察名單": [], "待觀察": []}


def _save_watchlists(wl: Dict[str, List[str]]) -> None:
    payload = json.dumps(json.dumps(wl, ensure_ascii=False))
    _js_eval(
        f'localStorage.setItem("{LOCAL_STORAGE_WATCHLISTS_KEY}", {payload})',
        "ls_write_watchlists",
    )


# ---------------------------------------------------------------------------
# Score history helpers
# ---------------------------------------------------------------------------

def _load_score_history() -> Dict:
    raw = _js_eval(
        f'localStorage.getItem("{LOCAL_STORAGE_SCORE_HISTORY_KEY}")',
        "ls_read_score_history",
    )
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _save_score_history(history: Dict) -> None:
    payload = json.dumps(json.dumps(history, ensure_ascii=False))
    _js_eval(
        f'localStorage.setItem("{LOCAL_STORAGE_SCORE_HISTORY_KEY}", {payload})',
        "ls_write_score_history",
    )


# ---------------------------------------------------------------------------
# Alerts helpers
# ---------------------------------------------------------------------------

def _load_alerts() -> Dict[str, Dict]:
    raw = _js_eval(
        f'localStorage.getItem("{LOCAL_STORAGE_ALERTS_KEY}")',
        "ls_read_alerts",
    )
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _save_alerts(alerts: Dict[str, Dict]) -> None:
    payload = json.dumps(json.dumps(alerts, ensure_ascii=False))
    _js_eval(
        f'localStorage.setItem("{LOCAL_STORAGE_ALERTS_KEY}", {payload})',
        "ls_write_alerts",
    )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="台股量化評分 UI", layout="wide")
    st.title("台股量化評分與推薦")
    st.caption("精簡主畫面：先看結論，細節可展開查看。資料來源：Yahoo Finance。")

    # ---- Sidebar ----
    with st.sidebar:
        st.subheader("輸入設定")

        # 自選股清單
        st.markdown("---")
        st.markdown("**自選股清單**")
        watchlists = _load_watchlists()
        wl_names = list(watchlists.keys())
        selected_wl = st.selectbox("選擇清單", ["（不使用）"] + wl_names, key="wl_select")

        col_wl1, col_wl2 = st.columns(2)
        with col_wl1:
            new_wl_name = st.text_input("新增清單名稱", key="new_wl_name", label_visibility="collapsed", placeholder="新清單名稱...")
        with col_wl2:
            if st.button("新增清單") and new_wl_name and new_wl_name not in watchlists:
                watchlists[new_wl_name] = []
                _save_watchlists(watchlists)
                st.rerun()

        if selected_wl != "（不使用）" and selected_wl in watchlists:
            if st.button(f"刪除「{selected_wl}」清單"):
                del watchlists[selected_wl]
                _save_watchlists(watchlists)
                st.rerun()

        st.markdown("---")

        _ensure_ticker_input_from_local_storage()

        # 如果選了自選股清單，自動填入
        if selected_wl != "（不使用）" and selected_wl in watchlists and watchlists[selected_wl]:
            wl_tickers = ",".join(t.replace(".TW", "") for t in watchlists[selected_wl])
            st.session_state["ticker_input"] = wl_tickers

        ticker_text = st.text_input(
            "台股代號（逗號分隔）",
            key="ticker_input",
            help="會自動記在瀏覽器 localStorage，下次開啟會還原。",
        )
        profile = st.radio("投資風格", ["保守", "平衡", "積極"], index=1, horizontal=True)
        remember = st.checkbox("計算成功後記住代號到瀏覽器", value=True)

        # 產業快速選擇
        st.markdown("---")
        st.markdown("**產業快選**")
        industry_choice = st.selectbox(
            "選擇產業自動帶入",
            ["（不使用）"] + list(INDUSTRY_MAP.keys()),
            key="industry_select",
        )
        if industry_choice != "（不使用）":
            industry_tickers = ",".join(t.replace(".TW", "") for t in INDUSTRY_MAP[industry_choice])
            if st.button(f"帶入 {industry_choice} 股票"):
                st.session_state["ticker_input"] = industry_tickers
                st.rerun()

        st.markdown("---")
        # 回測設定
        st.markdown("**回測設定**")
        backtest_months = st.selectbox("回測期間（月）", [6, 12, 24], index=1, key="bt_months")

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("開始計算", type="primary"):
                st.session_state["should_run"] = True
        with col_b:
            if st.button("清除記憶"):
                _clear_tickers_local_storage()
                st.session_state["ticker_input"] = DEFAULT_TICKER_TEXT
                st.session_state["should_run"] = False
                st.rerun()

    if not st.session_state.get("should_run", False):
        st.info("調整完設定後，按「開始計算」。")
        return

    tickers = normalize_tickers(ticker_text)
    if not tickers:
        st.error("請至少輸入一個代號。")
        return

    # ---- Data fetching ----
    metrics = []
    fundamentals: Dict[str, FundamentalMetrics] = {}
    chart_close_map: Dict[str, pd.Series] = {}
    forecast_map: Dict[str, Dict[str, float]] = {}
    ohlc_map: Dict[str, pd.DataFrame] = {}
    tech_signals: Dict[str, TechnicalSignals] = {}
    errors = []

    with st.spinner("下載資料與計算中..."):
        for t in tickers:
            try:
                metrics.append(calculate_price_metrics(t))
                info = fetch_ticker_info(t)
                fundamentals[t] = score_fundamental_from_info(t, info)
                chart_close_map[t] = fetch_close_series(t, "3y")
                forecast_map[t] = calc_3day_forecast_from_close(fetch_close_series(t, "2y"))
                # 技術指標用 OHLC
                ohlc = fetch_ohlc(t, "1y")
                ohlc_map[t] = ohlc
                tech_signals[t] = compute_technical_signals(t, ohlc)
            except Exception as exc:
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

    # 自選股：存入當前清單
    if selected_wl != "（不使用）" and selected_wl in watchlists:
        watchlists[selected_wl] = tickers
        _save_watchlists(watchlists)

    scored = build_scores(metrics, fundamentals, profile)

    # ---- Score history tracking ----
    today_str = pd.Timestamp.now().strftime("%Y-%m-%d")
    score_history = _load_score_history()
    current_scores = {}
    for _, row in scored.iterrows():
        current_scores[row["ticker"]] = round(float(row["total_score"]), 2)
    score_history[today_str] = current_scores
    _save_score_history(score_history)

    # 計算分數變化
    prev_scores = {}
    sorted_dates = sorted(score_history.keys())
    if len(sorted_dates) >= 2:
        prev_date = sorted_dates[-2]
        prev_scores = score_history[prev_date]

    # ---- Check alerts ----
    alerts = _load_alerts()
    triggered_alerts = []
    for t in scored["ticker"].tolist():
        if t not in alerts:
            continue
        a = alerts[t]
        row = scored[scored["ticker"] == t].iloc[0]
        ts = tech_signals.get(t)
        # 總分警示
        if "score_above" in a and row["total_score"] >= a["score_above"]:
            triggered_alerts.append(
                (t, "success", f"總分 {row['total_score']:.1f} >= {a['score_above']}（達到推薦門檻）")
            )
        if "score_below" in a and row["total_score"] <= a["score_below"]:
            triggered_alerts.append(
                (t, "warning", f"總分 {row['total_score']:.1f} <= {a['score_below']}（低於警戒門檻）")
            )
        # 價格警示
        if "price_above" in a and a["price_above"] > 0 and row["last"] >= a["price_above"]:
            triggered_alerts.append(
                (t, "success", f"股價 {row['last']:.2f} >= {a['price_above']}（突破目標價）")
            )
        if "price_below" in a and a["price_below"] > 0 and row["last"] <= a["price_below"]:
            triggered_alerts.append(
                (t, "warning", f"股價 {row['last']:.2f} <= {a['price_below']}（跌破支撐價）")
            )
        # RSI 警示
        if ts:
            if a.get("rsi_overbought") and ts.rsi >= 70:
                triggered_alerts.append(
                    (t, "warning", f"RSI {ts.rsi:.1f} >= 70（超買警示）")
                )
            if a.get("rsi_oversold") and ts.rsi <= 30:
                triggered_alerts.append(
                    (t, "success", f"RSI {ts.rsi:.1f} <= 30（超賣，可能有反彈機會）")
                )

    # ---- Display alerts at top ----
    if triggered_alerts:
        st.subheader("觸發的警示")
        for ticker, level, msg in triggered_alerts:
            if level == "success":
                st.success(f"{ticker}: {msg}")
            else:
                st.warning(f"{ticker}: {msg}")
        st.markdown("---")

    # ---- Prepare display data ----
    display_cols = ["ticker", "last", "total_score", "recommendation"]
    detail_cols = [
        "ticker", "fundamental", "price_score",
        "ret_1y", "ret_3y", "vol_1y", "vol_3y",
        "mdd_1y", "mdd_3y", "sharpe_1y", "sharpe_3y",
    ]
    summary_view = scored[display_cols].copy()
    detail_view = scored[detail_cols].copy()
    pct_cols = ["ret_1y", "ret_3y", "vol_1y", "vol_3y", "mdd_1y", "mdd_3y"]
    for c in pct_cols:
        detail_view[c] = detail_view[c].apply(as_pct)
    summary_view["last"] = summary_view["last"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    summary_view["total_score"] = summary_view["total_score"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

    # 加入分數變化欄位
    if prev_scores:
        changes = []
        for _, row in scored.iterrows():
            t = row["ticker"]
            prev = prev_scores.get(t)
            if prev is not None:
                diff = row["total_score"] - prev
                if diff > 0:
                    changes.append(f"↑{diff:.1f}")
                elif diff < 0:
                    changes.append(f"↓{abs(diff):.1f}")
                else:
                    changes.append("→")
            else:
                changes.append("新")
        summary_view["變化"] = changes

    for c in ["fundamental", "price_score", "sharpe_1y", "sharpe_3y"]:
        detail_view[c] = detail_view[c].map(lambda x: f"{x:.2f}" if pd.notna(x) else "-")

    top = scored.iloc[0]

    # ---- Tabs ----
    tabs = st.tabs([
        "總覽", "技術指標", "產業比較", "預測",
        "回測", "圖表", "進階資料", "警示設定",
    ])

    # === Tab 0: 總覽 ===
    with tabs[0]:
        st.subheader("量化排名（精簡）")
        st.dataframe(summary_view, width="stretch", hide_index=True)
        st.success(
            f"目前第一名：{top['ticker']} | 總分 {top['total_score']:.1f} | {top['recommendation']}"
        )

    # === Tab 1: 技術指標 ===
    with tabs[1]:
        st.subheader("技術指標分析 (RSI / MACD / KD)")
        if not tech_signals:
            st.warning("無技術指標資料。")
        else:
            # 指標總覽表
            tech_rows = []
            for t in scored["ticker"].tolist():
                ts = tech_signals.get(t)
                if not ts:
                    continue
                tech_rows.append({
                    "代號": ts.ticker,
                    "RSI(14)": f"{ts.rsi:.1f}",
                    "RSI訊號": ts.rsi_signal,
                    "MACD": f"{ts.macd:.2f}",
                    "MACD訊號": ts.macd_signal,
                    "K值": f"{ts.k:.1f}",
                    "D值": f"{ts.d:.1f}",
                    "KD訊號": ts.kd_signal,
                })
            st.dataframe(pd.DataFrame(tech_rows), width="stretch", hide_index=True)

            # 個股技術指標圖
            st.markdown("---")
            selected_tech = st.selectbox(
                "選擇股票檢視走勢圖",
                [t for t in scored["ticker"].tolist() if t in ohlc_map],
                key="tech_chart_select",
            )
            if selected_tech and selected_tech in ohlc_map:
                ohlc = ohlc_map[selected_tech]
                close = ohlc["Close"]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**RSI (14)**")
                    rsi_s = calc_rsi(close)
                    rsi_df = pd.DataFrame({"RSI": rsi_s, "超買(70)": 70, "超賣(30)": 30})
                    st.line_chart(rsi_df, width="stretch")

                with col2:
                    st.markdown("**KD (9,3)**")
                    kd_df = calc_kd(ohlc["High"], ohlc["Low"], close)
                    st.line_chart(kd_df, width="stretch")

                st.markdown("**MACD (12,26,9)**")
                macd_df = calc_macd(close)
                st.line_chart(macd_df[["MACD", "Signal"]], width="stretch")
                st.bar_chart(macd_df["Histogram"], width="stretch")

    # === Tab 2: 產業比較 ===
    with tabs[2]:
        st.subheader("產業/類股比較")
        # 判斷當前股票屬於哪些產業
        current_tickers_set = set(tickers)
        matched_industries = []
        for ind_name, ind_tickers in INDUSTRY_MAP.items():
            if current_tickers_set & set(ind_tickers):
                matched_industries.append(ind_name)

        if matched_industries:
            st.info(f"當前股票涵蓋的產業：{', '.join(matched_industries)}")

        compare_industry = st.selectbox(
            "選擇產業進行比較",
            list(INDUSTRY_MAP.keys()),
            key="compare_industry",
        )
        if compare_industry:
            ind_tickers = INDUSTRY_MAP[compare_industry]
            st.caption(f"產業成分股：{', '.join(ind_tickers)}")

            # 顯示已在列表中的股票分數
            in_list = [t for t in ind_tickers if t in set(scored["ticker"].tolist())]
            not_in_list = [t for t in ind_tickers if t not in set(scored["ticker"].tolist())]

            if in_list:
                ind_scored = scored[scored["ticker"].isin(in_list)][
                    ["ticker", "fundamental", "price_score", "total_score", "recommendation"]
                ].copy()
                ind_scored = ind_scored.sort_values("total_score", ascending=False)
                st.markdown("**已計算的產業成分股排名**")
                st.dataframe(ind_scored, width="stretch", hide_index=True)

                # 多維度分數比較
                if len(in_list) >= 2:
                    st.markdown("**多維度分數比較**")
                    radar_data = scored[scored["ticker"].isin(in_list)][
                        ["ticker", "s_ret_3y", "s_vol_3y", "s_mdd_3y", "s_sharpe_3y", "fundamental"]
                    ].copy()
                    radar_data.columns = ["ticker", "報酬", "低波動", "低回撤", "Sharpe", "基本面"]
                    radar_data = radar_data.set_index("ticker")
                    st.bar_chart(radar_data, width="stretch")

            if not_in_list:
                st.caption(f"以下成分股未在計算清單中：{', '.join(not_in_list)}。可將它們加入代號欄位一起計算。")

    # === Tab 3: 預測 ===
    with tabs[3]:
        st.subheader("3天機率預測")
        forecast_rows = []
        for t in scored["ticker"].tolist():
            f3 = forecast_map.get(t)
            if not f3:
                forecast_rows.append({
                    "ticker": t, "p_up_3d": "-", "p_down_3d": "-",
                    "exp_3d_ret": "-", "range_10_90": "資料不足",
                })
                continue
            forecast_rows.append({
                "ticker": t,
                "p_up_3d": as_pct(f3["p_up_3d"]),
                "p_down_3d": as_pct(f3["p_down_3d"]),
                "exp_3d_ret": as_pct(f3["exp_3d_ret"]),
                "range_10_90": f"{as_pct(f3['q10'])} ~ {as_pct(f3['q90'])}",
            })
        st.dataframe(pd.DataFrame(forecast_rows), width="stretch", hide_index=True)
        st.caption("此預測是統計機率模型，非保證結果。")

    # === Tab 4: 回測 ===
    with tabs[4]:
        st.subheader(f"回測分析（{backtest_months} 個月）")
        if len(chart_close_map) < 1:
            st.warning("無足夠資料進行回測。")
        else:
            try:
                # 用 0050 作為基準
                bench_close = fetch_close_series("0050.TW", "3y")
                bt = run_backtest(chart_close_map, bench_close, months=backtest_months)

                # 績效摘要
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("累積報酬", f"{bt.cumulative_return * 100:.2f}%")
                col2.metric("年化報酬", f"{bt.annualized_return * 100:.2f}%")
                col3.metric("最大回撤", f"{bt.max_drawdown * 100:.2f}%")
                col4.metric("Sharpe", f"{bt.sharpe:.2f}")

                col5, col6 = st.columns(2)
                col5.metric("月勝率", f"{bt.win_rate * 100:.1f}%")

                # 淨值曲線
                st.markdown("**策略 vs 大盤 (0050) 淨值曲線**")
                curve_df = pd.DataFrame({
                    "策略（等權配置）": bt.equity_curve,
                    "大盤 (0050)": bt.benchmark_curve,
                })
                st.line_chart(curve_df, width="stretch")

                # 月度報酬
                st.markdown("**月度報酬**")
                monthly_df = bt.monthly_returns.to_frame("月報酬")
                monthly_df["月報酬"] = monthly_df["月報酬"].apply(lambda x: f"{x * 100:.2f}%")
                monthly_df.index = monthly_df.index.strftime("%Y-%m")
                st.dataframe(monthly_df, width="stretch")

            except Exception as exc:
                st.error(f"回測失敗：{exc}")

    # === Tab 5: 圖表 ===
    with tabs[5]:
        st.subheader("圖表：3年價格、回撤、分數")
        if not chart_close_map:
            st.warning("目前無可用圖表資料。")
        else:
            price_df, drawdown_df = build_chart_data(chart_close_map)
            st.caption("價格圖採 3 年期、起點標準化為 100。")
            st.line_chart(price_df, width="stretch")
            st.caption("回撤圖（%）：越接近 0 代表距離歷史高點越近。")
            st.line_chart(drawdown_df, width="stretch")
            comp = scored[["ticker", "fundamental", "price_score", "total_score"]].copy()
            comp = comp.set_index("ticker")
            st.bar_chart(comp, width="stretch")

    # === Tab 6: 進階資料 ===
    with tabs[6]:
        st.subheader("完整量化指標")
        st.dataframe(detail_view, width="stretch", hide_index=True)
        f_rows = []
        for t in scored["ticker"].tolist():
            f = fundamentals.get(t)
            if not f:
                continue
            f_rows.append({
                "ticker": t,
                "type": f.quote_type,
                "pe": as_ratio(f.pe),
                "pb": as_ratio(f.pb),
                "dividend_yield": as_pct(f.dividend_yield),
                "roe": as_pct(f.roe),
                "debt_to_equity": as_ratio(f.debt_to_equity),
                "expense_ratio": as_pct(f.expense_ratio),
                "fundamental_score": f"{f.score:.2f}",
            })
        st.subheader("基本面自動抓取")
        if f_rows:
            st.dataframe(pd.DataFrame(f_rows), width="stretch", hide_index=True)
        st.subheader("模型說明")
        st.markdown(
            """
            - 基本面分自動由 yfinance 指標估算（股票與 ETF 權重不同）
            - 總分依風格切換：保守/平衡/積極
            - 歷史股價因子包含：1Y/3Y 報酬、波動、最大回撤、Sharpe、均線趨勢
            - 技術指標：RSI(14)、MACD(12,26,9)、KD(9,3) 提供買賣訊號參考
            - 回測功能以等權配置模擬歷史績效
            - 3天預測為統計機率模型（非保證），僅供決策輔助
            - 這是決策輔助工具，不是投資建議
            """
        )

    # === Tab 7: 警示設定 ===
    with tabs[7]:
        st.subheader("警示條件設定")
        st.caption("設定的警示會在每次計算時自動檢查，觸發時顯示在總覽上方。")
        alert_ticker = st.selectbox(
            "選擇股票設定警示",
            scored["ticker"].tolist(),
            key="alert_ticker",
        )

        if alert_ticker:
            existing = alerts.get(alert_ticker, {})
            st.markdown(f"**{alert_ticker} 的警示設定**")

            col1, col2 = st.columns(2)
            with col1:
                score_above = st.number_input(
                    "總分 >= (推薦警示)",
                    value=float(existing.get("score_above", 65)),
                    step=1.0,
                    key="alert_score_above",
                )
                price_above = st.number_input(
                    "股價 >= (突破目標價)",
                    value=float(existing.get("price_above", 0)),
                    step=1.0,
                    key="alert_price_above",
                )
            with col2:
                score_below = st.number_input(
                    "總分 <= (警戒警示)",
                    value=float(existing.get("score_below", 40)),
                    step=1.0,
                    key="alert_score_below",
                )
                price_below = st.number_input(
                    "股價 <= (跌破支撐價)",
                    value=float(existing.get("price_below", 0)),
                    step=1.0,
                    key="alert_price_below",
                )

            rsi_overbought = st.checkbox(
                "RSI 超買警示 (>= 70)",
                value=existing.get("rsi_overbought", True),
                key="alert_rsi_ob",
            )
            rsi_oversold = st.checkbox(
                "RSI 超賣警示 (<= 30)",
                value=existing.get("rsi_oversold", True),
                key="alert_rsi_os",
            )

            if st.button("儲存警示", key="save_alert"):
                alerts[alert_ticker] = {
                    "score_above": score_above,
                    "score_below": score_below,
                    "price_above": price_above,
                    "price_below": price_below,
                    "rsi_overbought": rsi_overbought,
                    "rsi_oversold": rsi_oversold,
                }
                _save_alerts(alerts)
                st.success(f"已儲存 {alert_ticker} 的警示設定。")

            # 顯示所有已設定的警示
            if alerts:
                st.markdown("---")
                st.markdown("**所有已設定的警示**")
                alert_rows = []
                for t, a in alerts.items():
                    alert_rows.append({
                        "代號": t,
                        "總分>=": a.get("score_above", "-"),
                        "總分<=": a.get("score_below", "-"),
                        "股價>=": a.get("price_above", "-"),
                        "股價<=": a.get("price_below", "-"),
                        "RSI超買": "是" if a.get("rsi_overbought") else "否",
                        "RSI超賣": "是" if a.get("rsi_oversold") else "否",
                    })
                st.dataframe(pd.DataFrame(alert_rows), width="stretch", hide_index=True)

                if st.button("清除所有警示"):
                    _save_alerts({})
                    st.success("已清除所有警示。")


if __name__ == "__main__":
    main()
