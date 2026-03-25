from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("user_id", "ticker", name="uq_alert_user_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    score_above: Mapped[float | None] = mapped_column(Numeric(6, 2))
    score_below: Mapped[float | None] = mapped_column(Numeric(6, 2))
    price_above: Mapped[float | None] = mapped_column(Numeric(12, 2))
    price_below: Mapped[float | None] = mapped_column(Numeric(12, 2))
    rsi_overbought: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    rsi_oversold: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="alerts")
