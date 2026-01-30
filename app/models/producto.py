from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"), nullable=True)

    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sku: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    precio: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    costo: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    stock_actual: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    stock_minimo: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())