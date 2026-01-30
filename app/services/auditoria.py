from sqlalchemy.orm import Session
from app.models.log_auditoria import LogAuditoria

def log_event(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    accion: str,
    entidad: str | None = None,
    entidad_id: int | None = None,
    detalle: dict | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.add(LogAuditoria(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
        ip=ip,
        user_agent=user_agent,
    ))
