from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class InventarioMovimiento(Base):
    __tablename__ = "inventario_movimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)

    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # entrada|salida|ajuste|venta
    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    costo_unitario: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())