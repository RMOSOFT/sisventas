from sqlalchemy import DateTime, Integer, String, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    empresa_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="CASCADE"), index=True, nullable=False)

    # SALE, CANCEL_SALE, IN, OUT, ADJUST, RETURN...
    tipo: Mapped[str] = mapped_column(String(30), index=True, nullable=False)

    # cantidad positiva o negativa (tu eliges, pero sé consistente)
    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    stock_before: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock_after: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    ref_tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)   # "venta", "ajuste"
    ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)

    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)