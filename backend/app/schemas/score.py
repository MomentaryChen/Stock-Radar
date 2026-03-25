from pydantic import BaseModel


class ComputeScoresRequest(BaseModel):
    tickers: list[str]
    profile: str = "平衡"


class ScoredTicker(BaseModel):
    ticker: str
    last: float
    total_score: float
    fundamental: float
    price_score: float
    recommendation: str
    ret_1y: float
    ret_3y: float
    vol_1y: float
    vol_3y: float
    mdd_1y: float
    mdd_3y: float
    sharpe_1y: float
    sharpe_3y: float


class FundamentalDetail(BaseModel):
    ticker: str
    quote_type: str
    pe: float | None
    pb: float | None
    dividend_yield: float | None
    roe: float | None
    debt_to_equity: float | None
    expense_ratio: float | None
    total_assets: float | None
    score: float


class TriggeredAlert(BaseModel):
    ticker: str
    level: str  # "success" | "warning"
    message: str


class ComputeScoresResponse(BaseModel):
    scores: list[ScoredTicker]
    fundamentals: list[FundamentalDetail]
    triggered_alerts: list[TriggeredAlert]
