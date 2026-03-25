"""Scoring service: orchestrates data fetch, metrics computation, and score persistence."""

from datetime import date

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.repositories.alert_repo import AlertRepo
from backend.app.repositories.score_history_repo import ScoreHistoryRepo
from backend.app.schemas.score import (
    ComputeScoresResponse,
    FundamentalDetail,
    ScoredTicker,
    TriggeredAlert,
)
from backend.app.services.market_data_service import MarketDataService
from backend.core.metrics import FundamentalMetrics, PriceMetrics, calculate_price_metrics
from backend.core.scoring import build_scores, score_fundamental_from_info
from backend.core.technical import TechnicalSignals, compute_technical_signals

DEFAULT_USER_ID = 1


class ScoringService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mds = MarketDataService(session)
        self.score_repo = ScoreHistoryRepo(session)
        self.alert_repo = AlertRepo(session)

    async def compute(self, tickers: list[str], profile: str) -> ComputeScoresResponse:
        metrics_list: list[PriceMetrics] = []
        fundamentals: dict[str, FundamentalMetrics] = []
        tech_signals: dict[str, TechnicalSignals] = {}
        fundamental_details: list[FundamentalDetail] = []
        errors: list[str] = []

        fundamentals = {}

        for t in tickers:
            try:
                close_1y = await self.mds.get_close_series(t, "1y")
                close_3y = await self.mds.get_close_series(t, "3y")
                pm = calculate_price_metrics(t, close_1y, close_3y)
                metrics_list.append(pm)

                info = await self.mds.get_ticker_info(t)
                fm = score_fundamental_from_info(t, info)
                fundamentals[t] = fm
                fundamental_details.append(FundamentalDetail(
                    ticker=t,
                    quote_type=fm.quote_type,
                    pe=fm.pe,
                    pb=fm.pb,
                    dividend_yield=fm.dividend_yield,
                    roe=fm.roe,
                    debt_to_equity=fm.debt_to_equity,
                    expense_ratio=fm.expense_ratio,
                    total_assets=fm.total_assets,
                    score=fm.score,
                ))

                # Technical signals for alert evaluation
                ohlc = await self.mds.get_ohlc(t, "1y")
                tech_signals[t] = compute_technical_signals(t, ohlc)

            except Exception as exc:
                errors.append(f"{t}: {exc}")

        if not metrics_list:
            return ComputeScoresResponse(scores=[], fundamentals=[], triggered_alerts=[])

        scored_df = build_scores(metrics_list, fundamentals, profile)

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
            )
        await self.score_repo.flush()

        # Build response
        scores = []
        for _, row in scored_df.iterrows():
            scores.append(ScoredTicker(
                ticker=row["ticker"],
                last=round(float(row["last"]), 2),
                total_score=round(float(row["total_score"]), 2),
                fundamental=round(float(row["fundamental"]), 2),
                price_score=round(float(row["price_score"]), 2),
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
        )

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
