import math
from typing import Optional

import numpy as np


RISK_FREE_RATE = 0.015


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


def normalize_ratio(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    if v > 1.0:
        return v / 100.0
    return v


def as_pct(v: Optional[float]) -> str:
    if v is None or np.isnan(v):
        return "-"
    return f"{v * 100:.2f}%"


def as_ratio(v: Optional[float]) -> str:
    if v is None or np.isnan(v):
        return "-"
    return f"{v:.2f}"
