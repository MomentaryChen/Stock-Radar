from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.schemas.score import ComputeScoresRequest, ComputeScoresResponse
from backend.app.services.scoring_service import ScoringService

router = APIRouter(prefix="/scores", tags=["scores"])


def _normalize_tickers(raw: list[str]) -> list[str]:
    normalized = []
    for p in raw:
        p = p.strip()
        if not p:
            continue
        if p.endswith(".TW"):
            normalized.append(p)
        elif p.isdigit():
            normalized.append(f"{p}.TW")
        else:
            normalized.append(p)
    return normalized


@router.post("/compute", response_model=ComputeScoresResponse)
async def compute_scores(req: ComputeScoresRequest, db: AsyncSession = Depends(get_db)):
    tickers = _normalize_tickers(req.tickers)
    if not tickers:
        return ComputeScoresResponse(scores=[], fundamentals=[], triggered_alerts=[])
    svc = ScoringService(db)
    return await svc.compute(tickers, req.profile)
