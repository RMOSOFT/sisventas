from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )

    accion: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    entidad: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    entidad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv4/IPv6
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    