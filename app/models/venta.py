from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)  # correlativo por empresa

    fecha: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    descuento_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    metodo_pago: Mapped[str] = mapped_column(String(50), nullable=False, default="efectivo")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="emitida")

    cliente_id = mapped_column(ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)

    cash_session_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    efectivo_recibido: Mapped[float] = mapped_column(Numeric(12,2), nullable=False, default=0)
    vuelto: Mapped[float] = mapped_column(Numeric(12,2), nullable=False, default=0)
    tipo_comprobante: Mapped[str] = mapped_column(String(2), nullable=False, server_default="B")  # B o F
    serie: Mapped[str] = mapped_column(String(4), nullable=False, server_default="B001")         # B001 / F001
    correlativo: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")        # correlativo por serie