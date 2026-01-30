from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, or_

from app.core.deps import get_db
from app.auth.deps import require_admin
from app.models.usuario import Usuario
from app.models.admin_history import AdminHistory # Modelo

# 🔹 DEFINICIÓN DEL ROUTER (esto faltaba)
router = APIRouter(prefix="/history", tags=["admin_history"])

# Agregar EVENT_LABELS + event_label en tu endpoint
EVENT_LABELS = {
    "access_request": "Solicitud de acceso",
    "access_approved": "Acceso aprobado",
    "access_denied": "Acceso denegado",
    "sale_issued": "Venta emitida",
    "sale_cancelled": "Venta anulada",
}

@router.get("")
def list_history(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),

    q: str | None = Query(default=None),
    actor_id: int | None = Query(default=None),
    target_id: int | None = Query(default=None),
    event: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
):
    Actor = aliased(Usuario)
    Target = aliased(Usuario)

    stmt = (
        select(
            AdminHistory,
            Actor.nombre.label("actor_nombre"),
            Actor.apellido.label("actor_apellido"),
            Target.nombre.label("target_nombre"),
            Target.apellido.label("target_apellido"),
        )
        .outerjoin(Actor, Actor.id == AdminHistory.actor_user_id)
        .outerjoin(Target, Target.id == AdminHistory.target_user_id)
        .where(AdminHistory.empresa_id == admin.empresa_id)
        .order_by(AdminHistory.id.desc())
        .limit(limit)
    )

    if event:
        stmt = stmt.where(AdminHistory.event == event)

    if actor_id:
        stmt = stmt.where(AdminHistory.actor_user_id == actor_id)

    if target_id:
        stmt = stmt.where(AdminHistory.target_user_id == target_id)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            AdminHistory.title.ilike(like),
            AdminHistory.message.ilike(like),
            AdminHistory.event.ilike(like),
        ))

    rows = db.execute(stmt).all()

    out = []
    for h, a_nom, a_ape, t_nom, t_ape in rows:
        out.append({
            "id": h.id,
            "event": h.event,
            "event_label": EVENT_LABELS.get(h.event, h.event), # Nuevo
            "title": h.title,
            "message": h.message,
            "created_at": str(h.created_at),

            "actor_user_id": h.actor_user_id,
            "actor_name": (f"{a_nom or ''} {a_ape or ''}").strip() or None,

            "target_user_id": h.target_user_id,
            "target_name": (f"{t_nom or ''} {t_ape or ''}").strip() or None,
        })
    return out

"""
@router.get("")
def list_history(
    db: Session = Depends(get_db), 
    admin: Usuario = Depends(require_admin),
    q: str | None = Query(default=None)): # Nuevo codigo para filtro ?q= (actor/target/event/title/message)
    
    stmt = select(AdminHistory).where(AdminHistory.empresa_id == admin.empresa_id)

    if q:
        qlike = f"%{q}%"
        stmt = stmt.where(or_(
            AdminHistory.event.ilike(qlike),
            AdminHistory.title.ilike(qlike),
            AdminHistory.message.ilike(qlike),
            cast(AdminHistory.actor_user_id, String).ilike(qlike),
            cast(AdminHistory.target_user_id, String).ilike(qlike),
        ))

    rows = db.execute(stmt.order_by(AdminHistory.id.desc()).limit(200)).scalars().all()

    
    #rows = db.execute(
    #    select(AdminHistory)
    #    .where(AdminHistory.empresa_id == admin.empresa_id)
    #    .order_by(AdminHistory.id.desc())
    #    .limit(100)
    #).scalars().all()

    return [
        {
            "id": x.id,
            "event": x.event,
            "title": x.title,
            "message": x.message,
            "actor_user_id": x.actor_user_id,
            "target_user_id": x.target_user_id,
            "created_at": str(x.created_at),
        } 
        for x in rows
    ]
"""