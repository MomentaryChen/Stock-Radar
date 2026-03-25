from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class MarketDataCache(Base):
    __tablename__ = "market_data_cache"
    __table_args__ = (UniqueConstraint("ticker", "trade_date", name="uq_mdc_ticker_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float | None] = mapped_column(Numeric(12, 4))
    high: Mapped[float | None] = mapped_column(Numeric(12, 4))
    low: Mapped[float | None] = mapped_column(Numeric(12, 4))
    close: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
