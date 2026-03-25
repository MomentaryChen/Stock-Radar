from sqlalchemy import ARRAY, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Industry(Base):
    __tablename__ = "industries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tickers: Mapped[list[str]] = mapped_column(ARRAY(String), server_default="{}", nullable=False)
