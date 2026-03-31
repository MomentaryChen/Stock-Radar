from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_db
from backend.app.schemas.news import NewsItem, NewsResponse
from backend.app.services.news_sentiment_service import NewsSentimentService
from backend.app.services.ticker_resolver_service import resolve_identifier_to_ticker

router = APIRouter(prefix="/news", tags=["news"])

@router.get("/{ticker}", response_model=NewsResponse)
async def get_news(
    ticker: str,
    limit: int = Query(20, ge=1, le=100),
    force_refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    resolved_ticker = await resolve_identifier_to_ticker(db, ticker)
    if not resolved_ticker:
        return NewsResponse(ticker="", count=0, items=[])
    svc = NewsSentimentService(db)
    rows = await svc.get_news(resolved_ticker, limit=limit, force_refresh=force_refresh)
    items = [NewsItem.model_validate(r) for r in rows]
    return NewsResponse(ticker=resolved_ticker, count=len(items), items=items)
