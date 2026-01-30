from sqlalchemy import DateTime, Integer, String, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    tipo_doc: Mapped[str] = mapped_column(String(10), nullable=False)        # DNI/RUC/CE
    num_doc: Mapped[str] = mapped_column(String(20), nullable=False)         # "12345678" / "20123456789"
    razon_social: Mapped[str] = mapped_column(String(160), nullable=False)   # nombre o razon social
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)

    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "num_doc", name="uq_clientes_empresa_num_doc"),
        Index("ix_clientes_empresa_num_doc", "empresa_id", "num_doc"),
        Index("ix_clientes_empresa_razon", "empresa_id", "razon_social"),
    )