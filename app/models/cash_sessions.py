from sqlalchemy import DateTime, Integer, String, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class CashSession(Base):
    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    status: Mapped[str] = mapped_column(String(10), default="open", index=True)  # open/closed

    opening_amount: Mapped[float] = mapped_column(Numeric(12,2), default=0, nullable=False)
    system_expected: Mapped[float] = mapped_column(Numeric(12,2), default=0, nullable=False)
    closing_amount_counted: Mapped[float | None] = mapped_column(Numeric(12,2), nullable=True)
    difference: Mapped[float | None] = mapped_column(Numeric(12,2), nullable=True)

    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    opened_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)