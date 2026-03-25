from pydantic import BaseModel


class AlertUpsert(BaseModel):
    score_above: float | None = None
    score_below: float | None = None
    price_above: float | None = None
    price_below: float | None = None
    rsi_overbought: bool = True
    rsi_oversold: bool = True


class AlertResponse(BaseModel):
    ticker: str
    score_above: float | None
    score_below: float | None
    price_above: float | None
    price_below: float | None
    rsi_overbought: bool
    rsi_oversold: bool

    model_config = {"from_attributes": True}
