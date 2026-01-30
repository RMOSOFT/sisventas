from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from fastapi import Request
from app.core.deps import get_db
from app.auth.deps import get_current_user, require_admin
from app.models import Usuario
from app.models.access_request import AccessRequest
from app.models.admin_history import AdminHistory
from app.services.history_service import push_history
from app.auth.deps import get_session_id

router = APIRouter(prefix="/access", tags=["access"])

@router.post("/request") # Aqui aumentamos el request
def create_request(payload: dict, request: Request, db: Session = Depends(get_db), 
    user: Usuario = Depends(get_current_user),
    sid: str = Depends(get_session_id)):# Nuevo codigo que estamos agregando

    recurso = (payload.get("recurso") or "").strip()
    motivo = (payload.get("motivo") or "").strip() or None
    # nueva linea de codigo aqui que estamos agregando
    sid = getattr(request.state, "sid", None)

    if recurso not in {"dashboard"}:
        raise HTTPException(status_code=400, detail="Recurso inválido")

    # Evitar spam: si ya hay una pending igual
    exists = db.execute(
        select(AccessRequest).where(
            AccessRequest.empresa_id == user.empresa_id,
            AccessRequest.user_id == user.id,
            AccessRequest.recurso == recurso,
            AccessRequest.status == "pending"
        )
    ).scalar_one_or_none()

    if exists:
        return {"ok": True, "already": True}

    req = AccessRequest(
        empresa_id=user.empresa_id,
        user_id=user.id,
        recurso=recurso,
        motivo=motivo,
        status="pending",
        session_id=sid,  # ✅ nuevo codigo de linea aqui
    )
    # Nuevo codigo aqui 
    """
    db.add(AdminHistory(
        empresa_id=user.empresa_id,
        event="access_request",
        title="Solicitud de acceso al Dashboard",
        message=f"El usuario #{user.id} solicitó acceso al Dashboard.",
        actor_user_id=user.id,
        target_user_id=user.id,
    ))"""
    db.add(req)
    db.commit()
    db.refresh(req)

    # Codigo que para la insercion para grabar los datos en la tabla admin_hitory
    push_history(
        db,
        empresa_id=user.empresa_id,
        event="access_request",
        title=f"Solicitud de acceso: {recurso}",
        message=motivo or "Sin motivo",
        actor_user_id=user.id,
        target_user_id=None,
    )

    return {"ok": True, "id": req.id}


@router.get("/requests")
def list_requests(db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    rows = db.execute(
        select(AccessRequest, Usuario)
        .join(Usuario, Usuario.id == AccessRequest.user_id)
        .where(
            AccessRequest.empresa_id == admin.empresa_id,
            AccessRequest.status == "pending",
        )
        .order_by(AccessRequest.id.desc())
    ).all()

    return [{
        "id": r.id,
        "recurso": r.recurso,
        "motivo": r.motivo,
        "created_at": str(r.created_at),
        "user": {
            "id": u.id,
            "nombre": u.nombre,
            "apellido": u.apellido,
            "email": u.email,
            "rol": u.rol,
        }
    } for (r, u) in rows]

"""
@router.get("/requests")
def list_requests(db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    rows = db.execute(
        select(AccessRequest).where(
            AccessRequest.empresa_id == admin.empresa_id,
            AccessRequest.status == "pending"
        ).order_by(AccessRequest.id.desc())
    ).scalars().all()

    return [{
        "id": r.id,
        "user_id": r.user_id,
        "recurso": r.recurso,
        "motivo": r.motivo,
        "created_at": str(r.created_at),
        "status": r.status
    } for r in rows]
"""

@router.post("/approve")
def approve(payload: dict, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    req_id = int(payload.get("id") or 0)
    r = db.execute(
        select(AccessRequest).where(
            AccessRequest.id == req_id,
            AccessRequest.empresa_id == admin.empresa_id
        )
    ).scalar_one_or_none()

    if not r or r.status != "pending":
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    r.status = "approved"
    r.approved_by = admin.id
    r.resolved_at = datetime.now(timezone.utc)
    db.commit()

    # Codigo que para la insercion para grabar los datos en la tabla admin_hitory
    push_history(
        db,
        empresa_id=admin.empresa_id,
        event="access_approved",
        title=f"Aprobado: {r.recurso}",
        message=f"Se aprobó solicitud #{r.id} del usuario_id={r.user_id}",
        actor_user_id=admin.id,
        target_user_id=r.user_id,
    )

    return {"ok": True}


@router.post("/deny")
def deny(payload: dict, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    req_id = int(payload.get("id") or 0)
    r = db.execute(
        select(AccessRequest).where(
            AccessRequest.id == req_id,
            AccessRequest.empresa_id == admin.empresa_id
        )
    ).scalar_one_or_none()

    if not r or r.status != "pending":
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    r.status = "denied"
    r.approved_by = admin.id
    r.resolved_at = datetime.now(timezone.utc)

    # Nuevo codigo aqui 
    db.add(AdminHistory(
        empresa_id=admin.empresa_id,
        event="approved",
        title="Acceso aprobado",
        message=f"Se aprobó acceso a '{r.recurso}' para usuario #{r.user_id}.",
        actor_user_id=admin.id,
        target_user_id=r.user_id,
    ))

    db.commit()

    # Codigo que para la insercion para grabar los datos en la tabla admin_hitory
    push_history(
        db,
        empresa_id=admin.empresa_id,
        event="access_denied",
        title=f"Denegado: {r.recurso}",
        message=f"Se denegó solicitud #{r.id} del usuario_id={r.user_id}",
        actor_user_id=admin.id,
        target_user_id=r.user_id,
    )

    return {"ok": True}