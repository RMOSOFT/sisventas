from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.schemas.venta import VentaCreate, VentaOut, VentaListOut, VentaDetailOut, VentaCancelIn
from app.crud import venta as crud
from app.models import Usuario, Empresa


router = APIRouter(prefix="/sales", tags=["sales"])

templates = Jinja2Templates(directory="app/web/templates")

# EMPRESA_ID = 1
# USER_ID = 1

# Funcion mejorada para crear ventas
@router.post("", response_model=VentaOut)
def create_sale(payload: VentaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    v = crud.create_sale(db, user.empresa_id, user.id, payload.model_dump())
    return {
        "id": v.id,
        "numero": v.numero,
        "total": float(v.total),
        "estado": v.estado,
        "can_cancel": True if user.rol == "admin" else True,  # luego afinamos regla
    }
"""
@router.post("", response_model=VentaOut)
def create_sale(payload: VentaCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    try:
        return crud.create_sale(db, user.empresa_id, user.id, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""

"""
@router.post("", response_model=VentaOut)
def create_sale(payload: VentaCreate, db: Session = Depends(get_db)):
    try:
        v = crud.create_sale(db, EMPRESA_ID, USER_ID, payload.model_dump())
        return v
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""


# Funcion mejorada para listar las ventas
@router.get("", response_model=list[VentaListOut])
def list_sales(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.list_sales(db, user.empresa_id, limit)
"""
@router.get("", response_model=list[VentaListOut])
def list_sales(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    return crud.list_sales(db, EMPRESA_ID, limit)
"""

# Funcion mejorada para detalles de la venta
@router.get("/{sale_id}", response_model=VentaDetailOut)
def sale_detail(sale_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    res = crud.get_sale_detail(db, user.empresa_id, sale_id)
    if not res:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    venta, items = res
    return {
        "id": venta.id,
        "numero": venta.numero,
        "fecha": venta.fecha,
        "subtotal": float(venta.subtotal),
        "descuento_total": float(venta.descuento_total),
        "total": float(venta.total),
        "metodo_pago": venta.metodo_pago,
        "estado": venta.estado,
        "items": items,
    }
"""
@router.get("/{sale_id}", response_model=VentaDetailOut)
def sale_detail(sale_id: int, db: Session = Depends(get_db)):
    res = crud.get_sale_detail(db, EMPRESA_ID, sale_id)
    if not res:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    venta, items = res
    return {
        "id": venta.id,
        "numero": venta.numero,
        "fecha": venta.fecha,
        "subtotal": float(venta.subtotal),
        "descuento_total": float(venta.descuento_total),
        "total": float(venta.total),
        "metodo_pago": venta.metodo_pago,
        "estado": venta.estado,
        "items": items,
    }
"""


# Funcion de endpoint para ver que salga la pagina de los tickets de ventas
@router.get("/{sale_id}/ticket", response_class=HTMLResponse)
def sale_ticket(sale_id: int, request: Request, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    res = crud.get_sale_detail(db, user.empresa_id, sale_id)
    if not res:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    venta, items = res

    empresa = db.get(Empresa, user.empresa_id)
    empresa_nombre = empresa.nombre if empresa else "Empresa"

    empresa_direccion = getattr(empresa, "direccion", None) if empresa else None
    empresa_telefono = getattr(empresa, "telefono", None) if empresa else None

    return templates.TemplateResponse(
        "admin/ticket_80mm.html",
        {
            "request": request,
            "empresa_nombre": empresa_nombre,
            "empresa_direccion": empresa_direccion,
            "empresa_telefono": empresa_telefono,
            "numero": venta.numero,
            "fecha": venta.fecha.strftime("%d/%m/%Y %I:%M %p"),
            "metodo_pago": venta.metodo_pago,
            "subtotal": float(venta.subtotal),
            "descuento_total": float(venta.descuento_total),
            "total": float(venta.total),
            "items": items,
        }
    )
"""
@router.get("/{sale_id}/ticket", response_class=HTMLResponse)
def sale_ticket(sale_id: int, request: Request, db: Session = Depends(get_db)):
    res = crud.get_sale_detail(db, EMPRESA_ID, sale_id)
    if not res:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    venta, items = res

    empresa = db.get(Empresa, EMPRESA_ID)
    empresa_nombre = empresa.nombre if empresa else "Empresa"

    # (opcionales: si luego agregas campos a Empresa)
    empresa_direccion = getattr(empresa, "direccion", None) if empresa else None
    empresa_telefono = getattr(empresa, "telefono", None) if empresa else None

    return templates.TemplateResponse(
        "ticket_80mm.html",
        {
            "request": request,
            "empresa_nombre": empresa_nombre,
            "empresa_direccion": empresa_direccion,
            "empresa_telefono": empresa_telefono,
            "numero": venta.numero,
            "fecha": venta.fecha.strftime("%d/%m/%Y %I:%M %p"),
            "metodo_pago": venta.metodo_pago,
            "subtotal": float(venta.subtotal),
            "descuento_total": float(venta.descuento_total),
            "total": float(venta.total),
            "items": items,
        }
    )
"""


# Funcion para cancelar los productos en ventas
@router.post("/{sale_id}/cancel")
def cancel_sale(sale_id: int, payload: VentaCancelIn, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    try:
        v = crud.cancel_sale(db, user.empresa_id, user.id, sale_id, payload.motivo)
        if not v:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return {"ok": True, "id": v.id, "estado": v.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
@router.post("/{sale_id}/cancel")
def cancel_sale(sale_id: int, payload: VentaCancelIn, db: Session = Depends(get_db)):
    try:
        v = crud.cancel_sale(db, EMPRESA_ID, sale_id, payload.motivo)
        if not v:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return {"ok": True, "id": v.id, "estado": v.estado}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""



