from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AdminHistory(Base):
    __tablename__ = "admin_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    event: Mapped[str] = mapped_column(String(40), nullable=False)   # "access_request", "approved", "denied"
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)

    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)   # quien hizo la acción
    target_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # a quién afecta

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)