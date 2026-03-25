from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class NewsSentiment(Base):
    __tablename__ = "news_sentiment"
    __table_args__ = (UniqueConstraint("url", name="uq_news_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sentiment_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    sentiment_label: Mapped[str] = mapped_column(String(10), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
