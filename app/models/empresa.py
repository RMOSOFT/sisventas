from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    ruc: Mapped[str | None] = mapped_column(String(11), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    web: Mapped[str | None] = mapped_column(String(120), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())