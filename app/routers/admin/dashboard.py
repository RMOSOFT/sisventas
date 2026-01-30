from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.core.deps import get_db
from app.auth.deps import get_current_user
from fastapi import Request
# from app.models.empresa import Empresa
from app.models import Venta, VentaDetalle, Producto, Usuario
from app.models.access_request import AccessRequest

#from app.models.access_request import AccessRequest

router = APIRouter(prefix="/dashboard", tags=["ad_dashboard"])
"""
def can_view_dashboard(db, user):
    if user.rol == "admin":
        return True
    ok = db.execute(
        select(AccessRequest).where(
            AccessRequest.empresa_id == user.empresa_id,
            AccessRequest.user_id == user.id,
            AccessRequest.recurso == "dashboard",
            AccessRequest.status == "approved",
        )
    ).scalar_one_or_none()
    return ok is not None
"""

def has_dashboard_access(db: Session, user: Usuario, sid: str | None) -> bool:# Nuevo codigo agregado sid: str | None
    if user.rol == "admin":
        return True

    # Nuevo codigo aqui
    if not sid:
        return False

    last = db.execute(
        select(AccessRequest)
        .where(
            AccessRequest.empresa_id == user.empresa_id,
            AccessRequest.user_id == user.id,
            AccessRequest.recurso == "dashboard",
            AccessRequest.status == "approved",
            AccessRequest.session_id == sid,  # ✅ CLAVE Nuevo codigo aqui
        )
        .order_by(AccessRequest.id.desc())
        .limit(1)
    ).scalar_one_or_none()

    return last is not None

"""
# Con esto: si el vendedor cierra sesión y vuelve a entrar, su sid cambia ⇒ pierde el acceso ⇒ debe solicitar otra vez.
@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    #if not can_view_dashboard(db, user):
        #raise HTTPException(403, "Acceso restringido")

    # Nuevo codigo aqui
    sid = getattr(request.state, "sid", None)

    if not has_dashboard_access(db, user, sid):# Nuevo codigo aqui sid
        raise HTTPException(status_code=403, detail="Acceso restringido al Dashboard")

    empresa_id = user.empresa_id

    ventas_total = db.execute(
        select(func.coalesce(func.sum(Venta.total), 0))
        .where(Venta.empresa_id == empresa_id, Venta.estado == "emitida")
    ).scalar_one()

    tickets = db.execute(
        select(func.count(Venta.id))
        .where(Venta.empresa_id == empresa_id, Venta.estado == "emitida")
    ).scalar_one()

    anuladas_total = db.execute(
        select(func.coalesce(func.sum(Venta.total), 0))
        .where(Venta.empresa_id == empresa_id, Venta.estado == "anulada")
    ).scalar_one()

    tickets_anulados = db.execute(
        select(func.count(Venta.id))
        .where(Venta.empresa_id == empresa_id, Venta.estado == "anulada")
    ).scalar_one()

    top = db.execute(
        select(Producto.nombre, func.coalesce(func.sum(VentaDetalle.cantidad), 0).label("qty"))
        .join(VentaDetalle, VentaDetalle.producto_id == Producto.id)
        .join(Venta, Venta.id == VentaDetalle.venta_id)
        .where(Producto.empresa_id == empresa_id, Venta.empresa_id == empresa_id, Venta.estado == "emitida")
        .group_by(Producto.nombre)
        .order_by(desc("qty"))
        .limit(5)
    ).all()

    return {
        "ventas_total": float(ventas_total),
        "tickets": int(tickets),
        "top_productos": [{"nombre": n, "cantidad": float(q)} for n, q in top],
    }
"""


# EMPRESA_ID = 1

# Funcion para todo el dashboard que sea vea segun las ventas
@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):


    # Nuevo codigo aqui
    sid = getattr(request.state, "sid", None)

    if not has_dashboard_access(db, user, sid):# Nuevo codigo aqui sid
        raise HTTPException(status_code=403, detail="Acceso restringido al Dashboard")

    empresa_id = user.empresa_id    


    # 1) Emitidas (lo real del negocio)
    ventas_total = db.execute(
        select(func.coalesce(func.sum(Venta.total), 0))
        .where(
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "emitida"
        )
    ).scalar_one()

    tickets = db.execute(
        select(func.count(Venta.id))
        .where(
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "emitida"
        )
    ).scalar_one()

    top = db.execute(
        select(Producto.nombre, func.coalesce(func.sum(VentaDetalle.cantidad), 0).label("qty"))
        .join(VentaDetalle, VentaDetalle.producto_id == Producto.id)
        .join(Venta, Venta.id == VentaDetalle.venta_id)
        .where(
            Producto.empresa_id == user.empresa_id,
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "emitida"
        )
        .group_by(Producto.nombre)
        .order_by(desc("qty"))
        .limit(5)
    ).all()

    # 2) Stock bajo (no depende de ventas)
    low = db.execute(
        select(Producto.id, Producto.nombre, Producto.stock_actual, Producto.stock_minimo)
        .where(
            Producto.empresa_id == user.empresa_id,
            Producto.activo == True,
            Producto.stock_actual <= Producto.stock_minimo
        )
        .limit(8)
    ).all()

    # 3) Auditoría de anulaciones (PRO)
    anuladas_total = db.execute(
        select(func.coalesce(func.sum(Venta.total), 0))
        .where(
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "anulada"
        )
    ).scalar_one()

    tickets_anulados = db.execute(
        select(func.count(Venta.id))
        .where(
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "anulada"
        )
    ).scalar_one()

    top_anulaciones = db.execute(
        select(Producto.nombre, func.coalesce(func.sum(VentaDetalle.cantidad), 0).label("qty"))
        .join(VentaDetalle, VentaDetalle.producto_id == Producto.id)
        .join(Venta, Venta.id == VentaDetalle.venta_id)
        .where(
            Producto.empresa_id == user.empresa_id,
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "anulada"
        )
        .group_by(Producto.nombre)
        .order_by(desc("qty"))
        .limit(5)
    ).all()

    ultimas_anuladas = db.execute(
        select(Venta.id, Venta.numero, Venta.fecha, Venta.total)
        .where(
            Venta.empresa_id == user.empresa_id,
            Venta.estado == "anulada"
        )
        .order_by(desc(Venta.fecha))
        .limit(5)
    ).all()

    return {
        # emitidas
        "ventas_total": float(ventas_total),
        "tickets": int(tickets),
        "top_productos": [{"nombre": n, "cantidad": float(q)} for n, q in top],

        # stock
        "stock_bajo": [{"id": i, "nombre": n, "stock": float(s), "min": float(m)} for i, n, s, m in low],

        # anulaciones (auditoría)
        "anuladas_total": float(anuladas_total),
        "tickets_anulados": int(tickets_anulados),
        "top_anulaciones": [{"nombre": n, "cantidad": float(q)} for n, q in top_anulaciones],
        "ultimas_anuladas": [
            {"id": i, "numero": int(num), "fecha": f.isoformat(), "total": float(t)}
            for i, num, f, t in ultimas_anuladas
        ],
    }


"""
@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    ventas_total = db.execute(
        select(func.coalesce(func.sum(Venta.total), 0)).where(Venta.empresa_id == EMPRESA_ID)
    ).scalar_one()
    tickets = db.execute(
        select(func.count(Venta.id)).where(Venta.empresa_id == EMPRESA_ID)
    ).scalar_one()

    top = db.execute(
        select(Producto.nombre, func.sum(VentaDetalle.cantidad).label("qty"))
        .join(VentaDetalle, VentaDetalle.producto_id == Producto.id)
        .join(Venta, Venta.id == VentaDetalle.venta_id)
        .where(Producto.empresa_id == EMPRESA_ID, Venta.empresa_id == EMPRESA_ID)
        .group_by(Producto.nombre)
        .order_by(desc("qty"))
        .limit(5)
    ).all()

    low = db.execute(
        select(Producto.id, Producto.nombre, Producto.stock_actual, Producto.stock_minimo)
        .where(Producto.empresa_id == EMPRESA_ID, Producto.activo == True, Producto.stock_actual <= Producto.stock_minimo)
        .limit(8)
    ).all()

    return {
        "ventas_total": float(ventas_total),
        "tickets": int(tickets),
        "top_productos": [{"nombre": n, "cantidad": float(q)} for n, q in top],
        "stock_bajo": [{"id": i, "nombre": n, "stock": float(s), "min": float(m)} for i, n, s, m in low],
    }

"""