from pydantic import BaseModel


class ForecastResponse(BaseModel):
    ticker: str
    p_up_3d: float
    p_down_3d: float
    exp_3d_ret: float
    q10: float
    q50: float
    q90: float
