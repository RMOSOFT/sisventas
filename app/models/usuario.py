from __future__ import annotations
from sqlalchemy import Boolean, DateTime, ForeignKey, Column, Integer, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# ROL_USUARIO = Enum("admin", "vendedor", name="rol_usuario")

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        # username único por empresa (recomendado)
        UniqueConstraint("empresa_id", "username", name="uq_usuario_empresa_username"),
        UniqueConstraint("empresa_id", "email", name="uq_usuario_empresa_email"),
    )
    

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

     # ✅ Login / identidad
    username: Mapped[str] = mapped_column(String(60), nullable=False)  # <- NUEVO

    # Datos personales (pro)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido: Mapped[str] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Seguridad
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), default="admin", nullable=False)
    #rol: Mapped[str] = mapped_column(ROL_USUARIO, nullable=False, default="vendedor")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Auditoría mínima
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    reset_token_expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
