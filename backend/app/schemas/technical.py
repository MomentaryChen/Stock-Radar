from pydantic import BaseModel


class TechnicalSignalResponse(BaseModel):
    ticker: str
    rsi: float
    rsi_signal: str
    macd: float
    macd_signal: str
    k: float
    d: float
    kd_signal: str


class TechnicalChartPoint(BaseModel):
    date: str
    value: float


class TechnicalChartResponse(BaseModel):
    ticker: str
    rsi_series: list[TechnicalChartPoint]
    macd_series: list[dict]
    kd_series: list[dict]
