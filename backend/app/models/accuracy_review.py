from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class AccuracyReview(Base):
    __tablename__ = "accuracy_review"
    __table_args__ = (
        UniqueConstraint("score_history_id", "review_days", name="uq_accuracy_review"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    score_history_id: Mapped[int] = mapped_column(
        ForeignKey("score_history.id", ondelete="CASCADE"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scored_date: Mapped[date] = mapped_column(Date, nullable=False)
    profile: Mapped[str] = mapped_column(String(10), nullable=False)
    review_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 3, 7, or 30
    score_at_time: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    price_at_score: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    price_at_review: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    return_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    is_accurate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    score_history = relationship("ScoreHistory")
