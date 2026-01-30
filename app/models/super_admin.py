from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class SuperAdmin(Base):
    __tablename__ = "super_admins"

    # Identidad
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Login
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)  # guardaremos minúsculas
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Reset password (token + expiración)
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())