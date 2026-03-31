"""Scoring service: orchestrates data fetch, metrics computation, and score persistence."""

import asyncio
from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import async_session
from backend.app.repositories.alert_repo import AlertRepo
from backend.app.repositories.score_history_repo import ScoreHistoryRepo
from backend.app.schemas.score import (
    ComputeScoresResponse,
    FundamentalDetail,
    ScoredTicker,
    TriggeredAlert,
)
from backend.app.services.market_data_service import MarketDataService
from backend.core import data as core_data
from backend.core.metrics import (
    FundamentalMetrics,
    PriceMetrics,
    calculate_price_metrics,
    calculate_volume_score,
)
from backend.core.scoring import build_scores, score_fundamental_from_info
from backend.core.technical import TechnicalSignals, compute_technical_signals

DEFAULT_USER_ID = 1
MAX_CONCURRENT_TICKERS = 10


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _resolve_localized_names(ticker: str, info: dict) -> tuple[str, str]:
    candidates = [
        str(info.get("longName") or ""),
        str(info.get("shortName") or ""),
        str(info.get("displayName") or ""),
    ]
    candidates = [c.strip() for c in candidates if c and c.strip()]
    if not candidates:
        return ticker, ticker

    zh = next((c for c in candidates if _has_cjk(c)), candidates[0])
    en = next((c for c in candidates if not _has_cjk(c)), candidates[0])
    return zh, en


def _normalize_ticker_code(ticker: str) -> str:
    return ticker.split(".")[0].strip().upper()


@dataclass
class _TickerComputeResult:
    ticker: str
    price_metrics: PriceMetrics | None = None
    fundamental: FundamentalMetrics | None = None
    technical: TechnicalSignals | None = None
    detail: FundamentalDetail | None = None
    name: str | None = None
    name_zh: str | None = None
    name_en: str | None = None
    volume_score: float | None = None
    error: str | None = None


class ScoringService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mds = MarketDataService(session)
        self.score_repo = ScoreHistoryRepo(session)
        self.alert_repo = AlertRepo(session)

    async def compute(self, tickers: list[str], profile: str) -> ComputeScoresResponse:
        metrics_list: list[PriceMetrics] = []
        fundamentals: dict[str, FundamentalMetrics] = {}
        volume_scores: dict[str, float] = {}
        tech_signals: dict[str, TechnicalSignals] = {}
        fundamental_details: list[FundamentalDetail] = []
        errors: list[str] = []

        ticker_names: dict[str, str] = {}
        ticker_names_zh: dict[str, str] = {}
        ticker_names_en: dict[str, str] = {}

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_TICKERS)
        results = await asyncio.gather(
            *(self._compute_single_ticker(t, semaphore) for t in tickers)
        )
        for res in results:
            if res.error:
                errors.append(res.error)
                continue
            if not res.price_metrics or not res.fundamental or not res.technical or not res.detail:
                errors.append(f"{res.ticker}: incomplete computation result")
                continue
            metrics_list.append(res.price_metrics)
            fundamentals[res.ticker] = res.fundamental
            tech_signals[res.ticker] = res.technical
            fundamental_details.append(res.detail)
            volume_scores[res.ticker] = float(res.volume_score if res.volume_score is not None else 50.0)
            ticker_names[res.ticker] = res.name or res.ticker
            ticker_names_zh[res.ticker] = res.name_zh or res.ticker
            ticker_names_en[res.ticker] = res.name_en or res.ticker

        if not metrics_list:
            return ComputeScoresResponse(scores=[], fundamentals=[], triggered_alerts=[], errors=errors)

        scored_df = build_scores(metrics_list, fundamentals, volume_scores, profile)

        # Persist score history
        today = date.today()
        for _, row in scored_df.iterrows():
            await self.score_repo.upsert(
                user_id=DEFAULT_USER_ID,
                ticker=row["ticker"],
                scored_date=today,
                profile=profile,
                total_score=round(float(row["total_score"]), 2),
                fundamental=round(float(row["fundamental"]), 2),
                price_score=round(float(row["price_score"]), 2),
                recommendation=row["recommendation"],
                price_at_score=round(float(row["last"]), 4),
            )
        await self.score_repo.flush()

        # Build response
        scores = []
        for _, row in scored_df.iterrows():
            scores.append(ScoredTicker(
                ticker=row["ticker"],
                name=ticker_names.get(row["ticker"], row["ticker"]),
                name_zh=ticker_names_zh.get(row["ticker"], row["ticker"]),
                name_en=ticker_names_en.get(row["ticker"], row["ticker"]),
                last=round(float(row["last"]), 2),
                total_score=round(float(row["total_score"]), 2),
                fundamental=round(float(row["fundamental"]), 2),
                price_score=round(float(row["price_score"]), 2),
                volume_score=round(float(row.get("volume_score", 50.0)), 2),
                recommendation=row["recommendation"],
                ret_1y=round(float(row["ret_1y"]), 4),
                ret_3y=round(float(row["ret_3y"]), 4),
                vol_1y=round(float(row["vol_1y"]), 4),
                vol_3y=round(float(row["vol_3y"]), 4),
                mdd_1y=round(float(row["mdd_1y"]), 4),
                mdd_3y=round(float(row["mdd_3y"]), 4),
                sharpe_1y=round(float(row["sharpe_1y"]), 4),
                sharpe_3y=round(float(row["sharpe_3y"]), 4),
            ))

        # Evaluate alerts
        triggered = await self._evaluate_alerts(scored_df, tech_signals)

        return ComputeScoresResponse(
            scores=scores,
            fundamentals=fundamental_details,
            triggered_alerts=triggered,
            errors=errors,
        )

    async def _compute_single_ticker(
        self, ticker: str, semaphore: asyncio.Semaphore
    ) -> _TickerComputeResult:
        async with semaphore:
            try:
                async with async_session() as session:
                    mds = MarketDataService(session)
                    close_1y = await mds.get_close_series(ticker, "1y")
                    close_3y = await mds.get_close_series(ticker, "3y")
                    price_metrics = calculate_price_metrics(ticker, close_1y, close_3y)

                    info = await mds.get_ticker_info(ticker)
                    cached_zh, cached_en, _ = await mds.get_ticker_profile(ticker)
                    if cached_zh and cached_en:
                        name_zh, name_en = cached_zh, cached_en
                    else:
                        name_zh, name_en = _resolve_localized_names(ticker, info)
                        if not _has_cjk(name_zh):
                            twse_map = await asyncio.to_thread(core_data.fetch_twse_name_map)
                            twse_name = twse_map.get(_normalize_ticker_code(ticker))
                            if twse_name:
                                name_zh = twse_name
                        source = "twse_openapi" if _has_cjk(name_zh) else "yfinance"
                        await mds.upsert_ticker_profile(
                            ticker=ticker, name_zh=name_zh, name_en=name_en, source=source
                        )

                    fundamental = score_fundamental_from_info(ticker, info)
                    detail = FundamentalDetail(
                        ticker=ticker,
                        name=name_zh,
                        name_zh=name_zh,
                        name_en=name_en,
                        quote_type=fundamental.quote_type,
                        pe=fundamental.pe,
                        pb=fundamental.pb,
                        dividend_yield=fundamental.dividend_yield,
                        roe=fundamental.roe,
                        debt_to_equity=fundamental.debt_to_equity,
                        expense_ratio=fundamental.expense_ratio,
                        total_assets=fundamental.total_assets,
                        score=fundamental.score,
                    )
                    ohlc = await mds.get_ohlc(ticker, "1y")
                    technical = compute_technical_signals(ticker, ohlc)
                    volume_score = calculate_volume_score(ohlc)

                    return _TickerComputeResult(
                        ticker=ticker,
                        price_metrics=price_metrics,
                        fundamental=fundamental,
                        technical=technical,
                        detail=detail,
                        name=name_zh,
                        name_zh=name_zh,
                        name_en=name_en,
                        volume_score=volume_score,
                    )
            except Exception as exc:
                return _TickerComputeResult(ticker=ticker, error=f"{ticker}: {exc}")

    async def _evaluate_alerts(
        self, scored_df: pd.DataFrame, tech_signals: dict[str, TechnicalSignals]
    ) -> list[TriggeredAlert]:
        alerts = await self.alert_repo.get_all(DEFAULT_USER_ID)
        alert_map = {a.ticker: a for a in alerts}
        triggered = []

        for _, row in scored_df.iterrows():
            t = row["ticker"]
            a = alert_map.get(t)
            if a is None:
                continue

            ts = tech_signals.get(t)
            total = float(row["total_score"])
            last = float(row["last"])

            if a.score_above is not None and total >= float(a.score_above):
                triggered.append(TriggeredAlert(
                    ticker=t, level="success",
                    message=f"總分 {total:.1f} >= {float(a.score_above)}（達到推薦門檻）",
                ))
            if a.score_below is not None and total <= float(a.score_below):
                triggered.append(TriggeredAlert(
                    ticker=t, level="warning",
                    message=f"總分 {total:.1f} <= {float(a.score_below)}（低於警戒門檻）",
                ))
            if a.price_above is not None and float(a.price_above) > 0 and last >= float(a.price_above):
                triggered.append(TriggeredAlert(
                    ticker=t, level="success",
                    message=f"股價 {last:.2f} >= {float(a.price_above)}（突破目標價）",
                ))
            if a.price_below is not None and float(a.price_below) > 0 and last <= float(a.price_below):
                triggered.append(TriggeredAlert(
                    ticker=t, level="warning",
                    message=f"股價 {last:.2f} <= {float(a.price_below)}（跌破支撐價）",
                ))
            if ts:
                if a.rsi_overbought and ts.rsi >= 70:
                    triggered.append(TriggeredAlert(
                        ticker=t, level="warning",
                        message=f"RSI {ts.rsi:.1f} >= 70（超買警示）",
                    ))
                if a.rsi_oversold and ts.rsi <= 30:
                    triggered.append(TriggeredAlert(
                        ticker=t, level="success",
                        message=f"RSI {ts.rsi:.1f} <= 30（超賣，可能有反彈機會）",
                    ))

        return triggered
