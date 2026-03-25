from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class ScoreHistory(Base):
    __tablename__ = "score_history"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", "scored_date", "profile", name="uq_score_history"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    scored_date: Mapped[date] = mapped_column(Date, nullable=False)
    profile: Mapped[str] = mapped_column(String(10), nullable=False)
    total_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    fundamental: Mapped[float | None] = mapped_column(Numeric(6, 2))
    price_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    recommendation: Mapped[str | None] = mapped_column(String(50))
    breakdown: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="score_histories")
