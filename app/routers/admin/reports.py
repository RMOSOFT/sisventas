from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.models import Usuario, Empresa

router = APIRouter(prefix="/reports", tags=["reports"])

# EMPRESA_ID = 1

# Funcion para el reporte de ventas por dia
@router.get("/sales-by-day")
def sales_by_day(
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    # Agrupa por fecha (día) y suma total
    q = text("""
        SELECT
          DATE(v.fecha) AS dia,
          COUNT(*) AS tickets,
          COALESCE(SUM(v.total), 0) AS total
        FROM ventas v
        WHERE v.empresa_id = :empresa_id
          AND v.estado = 'emitida'
          AND v.fecha >= NOW() - (:days || ' days')::interval
        GROUP BY DATE(v.fecha)
        ORDER BY dia ASC
    """)
    rows = db.execute(q, {"empresa_id": user.empresa_id, "days": days}).mappings().all()
    return [{"dia": str(r["dia"]), "tickets": int(r["tickets"]), "total": float(r["total"])} for r in rows]

# Funcion de productos mas vendidos
@router.get("/top-products")
def top_products(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    q = text("""
        SELECT
          p.id AS producto_id,
          p.nombre,
          COALESCE(SUM(d.cantidad), 0) AS cantidad,
          COALESCE(SUM(d.total_linea), 0) AS total
        FROM venta_detalle d
        JOIN ventas v ON v.id = d.venta_id
        JOIN productos p ON p.id = d.producto_id
        WHERE v.empresa_id = :empresa_id
          AND v.estado = 'emitida'
          AND v.fecha >= NOW() - (:days || ' days')::interval
        GROUP BY p.id, p.nombre
        ORDER BY cantidad DESC, total DESC
        LIMIT :limit
    """)
    rows = db.execute(q, {"empresa_id": user.empresa_id, "days": days, "limit": limit}).mappings().all()
    return [{"producto_id": int(r["producto_id"]), "nombre": r["nombre"], "cantidad": float(r["cantidad"]), "total": float(r["total"])} for r in rows]

# Funcion de producto menos cantidad vendida
@router.get("/bottom-products")
def bottom_products(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user)
):
    # Bottom = productos con menos cantidad vendida en el periodo (incluye 0 ventas)
    q = text("""
        SELECT
          p.id AS producto_id,
          p.nombre,
          COALESCE(SUM(d.cantidad), 0) AS cantidad,
          COALESCE(SUM(d.total_linea), 0) AS total
        FROM productos p
        LEFT JOIN venta_detalle d ON d.producto_id = p.id
        LEFT JOIN ventas v ON v.id = d.venta_id
          AND v.empresa_id = :empresa_id
          AND v.estado = 'emitida'
          AND v.fecha >= NOW() - (:days || ' days')::interval
        WHERE p.empresa_id = :empresa_id
          AND p.activo = true
        GROUP BY p.id, p.nombre
        ORDER BY cantidad ASC, total ASC
        LIMIT :limit
    """)
    rows = db.execute(q, {"empresa_id": user.empresa_id, "days": days, "limit": limit}).mappings().all()
    return [{"producto_id": int(r["producto_id"]), "nombre": r["nombre"], "cantidad": float(r["cantidad"]), "total": float(r["total"])} for r in rows]