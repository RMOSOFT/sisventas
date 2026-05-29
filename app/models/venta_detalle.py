from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class VentaDetalle(Base):
    __tablename__ = "venta_detalle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)

    cantidad: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    descuento: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_linea: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    