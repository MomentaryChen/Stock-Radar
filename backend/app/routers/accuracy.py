"""API router for accuracy review endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.services.accuracy_review_service import AccuracyReviewService

router = APIRouter(prefix="/accuracy", tags=["accuracy"])


@router.get("/summary")
async def get_accuracy_summary(
    profile: str | None = Query(None, description="Filter by scoring profile"),
    review_days: int | None = Query(None, description="Filter by review window (3, 7, or 30)"),
    session: AsyncSession = Depends(get_session),
):
    """Get aggregated accuracy statistics grouped by profile and review window."""
    svc = AccuracyReviewService(session)
    return await svc.get_summary(profile=profile, review_days=review_days)


@router.get("/details")
async def get_accuracy_details(
    profile: str | None = Query(None),
    review_days: int | None = Query(None),
    ticker: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get per-record accuracy details with optional filters."""
    svc = AccuracyReviewService(session)
    return await svc.get_details(
        profile=profile, review_days=review_days, ticker=ticker,
        limit=limit, offset=offset,
    )


@router.post("/run")
async def run_accuracy_review(
    review_date: date | None = Query(None, description="Override today's date for review"),
    session: AsyncSession = Depends(get_session),
):
    """Manually trigger accuracy review. Scheduled job also calls this daily."""
    svc = AccuracyReviewService(session)
    stats = await svc.run_review(today=review_date)
    return {"status": "completed", "stats": stats}
