from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    id: int
    ticker: str
    title: str
    url: str
    publisher: str | None
    published_at: datetime
    sentiment_score: float
    sentiment_label: str
    fetched_at: datetime

    model_config = {"from_attributes": True}


class NewsResponse(BaseModel):
    ticker: str
    count: int
    items: list[NewsItem]
