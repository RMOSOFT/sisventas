from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_, func

from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.models import Usuario, Producto
from app.models.stock_movement import StockMovement


# router = APIRouter(prefix="/inventory", tags=["kardex"])

router = APIRouter(prefix="/kardex", tags=["kardex"])

# EMPRESA_ID = 1

@router.get("")
def list_kardex(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    producto_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
):
    stmt = (
        select(
            StockMovement,
            Producto.nombre.label("producto_nombre")
        )
        .join(Producto, Producto.id == StockMovement.producto_id)
        .where(StockMovement.empresa_id == user.empresa_id)
        .order_by(desc(StockMovement.id))
        .limit(limit)
    )

    if producto_id:
        stmt = stmt.where(StockMovement.producto_id == producto_id)
    if tipo:
        stmt = stmt.where(StockMovement.tipo == tipo)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(func.coalesce(StockMovement.motivo, "").ilike(like))

    rows = db.execute(stmt).all()

    return [{
        "id": m.id,
        "producto_id": m.producto_id,
        "producto": prod,
        "tipo": m.tipo,
        "cantidad": float(m.cantidad),
        "before": float(m.stock_before),
        "after": float(m.stock_after),
        "ref_tipo": m.ref_tipo,
        "ref_id": m.ref_id,
        "motivo": m.motivo,
        "actor_user_id": m.actor_user_id,
        "created_at": str(m.created_at),
    } for m, prod in rows]


"""
@router.get("/kardex")
def kardex(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
    producto_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
):
    stmt = (
        select(
            StockMovement,
            Producto.nombre.label("producto_nombre")
        )
        .join(Producto, Producto.id == StockMovement.producto_id)
        .where(StockMovement.empresa_id == user.empresa_id)
        .order_by(desc(StockMovement.id))
        .limit(limit)
    )

    if producto_id:
        stmt = stmt.where(StockMovement.producto_id == producto_id)
    if tipo:
        stmt = stmt.where(StockMovement.tipo == tipo)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(and_(
            StockMovement.motivo.ilike(like)
        ))

    rows = db.execute(stmt).all()

    return [{
        "id": m.id,
        "producto_id": m.producto_id,
        "producto": prod,
        "tipo": m.tipo,
        "cantidad": float(m.cantidad),
        "before": float(m.stock_before),
        "after": float(m.stock_after),
        "ref_tipo": m.ref_tipo,
        "ref_id": m.ref_id,
        "motivo": m.motivo,
        "actor_user_id": m.actor_user_id,
        "created_at": str(m.created_at),
    } for m, prod in rows]


# Codigo para borrarlo si hay error
@router.get("")
def list_kardex(
    producto_id: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            StockMovement.id,
            StockMovement.created_at,
            StockMovement.tipo,
            StockMovement.cantidad,
            StockMovement.stock_before,
            StockMovement.stock_after,
            StockMovement.motivo,
            Producto.nombre.label("producto_nombre"),
        )
        .join(Producto, Producto.id == StockMovement.producto_id)
        .where(StockMovement.empresa_id == EMPRESA_ID)
        .order_by(desc(StockMovement.id))
        .limit(limit)
    )

    if producto_id:
        stmt = stmt.where(StockMovement.producto_id == producto_id)

    rows = db.execute(stmt).all()

    return [{
        "id": r.id,
        "created_at": str(r.created_at),
        "tipo": r.tipo,
        "cantidad": float(r.cantidad),
        "before": float(r.stock_before),
        "after": float(r.stock_after),
        "motivo": r.motivo,
        "producto": r.producto_nombre,
    } for r in rows]
"""





