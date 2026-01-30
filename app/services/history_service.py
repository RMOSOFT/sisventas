from sqlalchemy.orm import Session
from app.models.admin_history import AdminHistory

# Crear el “logger” de historial (función reusable)
def push_history(
    db: Session,
    *,
    empresa_id: int,
    event: str,
    title: str,
    message: str,
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
):
    row = AdminHistory(
        empresa_id=empresa_id,
        event=event,
        title=title,
        message=message,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
    )
    db.add(row)
    db.commit()

    return row