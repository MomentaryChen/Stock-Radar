from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.schemas.news import NewsItem, NewsResponse
from backend.app.services.news_sentiment_service import NewsSentimentService

router = APIRouter(prefix="/news", tags=["news"])

def _normalize_ticker(raw: str) -> str:
    p = raw.strip()
    if not p:
        return p
    if p.endswith(".TW"):
        return p
    if p.isdigit():
        return f"{p}.TW"
    return p


@router.get("/{ticker}", response_model=NewsResponse)
async def get_news(
    ticker: str,
    limit: int = Query(20, ge=1, le=100),
    force_refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    svc = NewsSentimentService(db)
    rows = await svc.get_news(_normalize_ticker(ticker), limit=limit, force_refresh=force_refresh)
    items = [NewsItem.model_validate(r) for r in rows]
    return NewsResponse(ticker=_normalize_ticker(ticker), count=len(items), items=items)
