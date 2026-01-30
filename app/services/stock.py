from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Producto
from app.models.stock_movement import StockMovement


def apply_stock_movement(
    db: Session,
    *,
    empresa_id: int,
    producto_id: int,
    tipo: str,
    cantidad: float,
    actor_user_id: int | None = None,
    ref_tipo: str | None = None,
    ref_id: int | None = None,
    motivo: str | None = None,
):
    # 1) Traer producto con lock (evita doble cobro simultáneo)
    p = db.execute(
        select(Producto)
        .where(Producto.id == producto_id, Producto.empresa_id == empresa_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not p:
        raise ValueError("Producto no existe")

    before = float(p.stock_actual or 0)
    after = before + float(cantidad)

    if after < 0:
        raise ValueError(f"Stock insuficiente para producto_id={producto_id}")

    # 2) Aplicar stock al producto
    p.stock_actual = after

    # 3) Guardar movimiento
    m = StockMovement(
        empresa_id=empresa_id,
        producto_id=producto_id,
        tipo=tipo,
        cantidad=float(cantidad),
        stock_before=before,
        stock_after=after,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        motivo=motivo,
        actor_user_id=actor_user_id,
    )
    db.add(m)
    db.flush()   # opcional pero recomendado
    return m




"""
def apply_stock_movement(
    db: Session,
    *,
    empresa_id: int,
    producto_id: int,
    tipo: str,
    cantidad: float,
    actor_user_id: int | None = None,
    ref_tipo: str | None = None,
    ref_id: int | None = None,
    motivo: str | None = None,
) -> StockMovement:
    # 1) leer producto (si quieres nivel PRO: lock FOR UPDATE)
    p = db.execute(
        select(Producto).where(
            Producto.id == producto_id,
            Producto.empresa_id == empresa_id
        )
    ).scalar_one()

    before = float(p.stock_actual or 0)
    after = before + float(cantidad)

    if after < 0:
        raise ValueError("Stock insuficiente para realizar el movimiento")

    # 2) actualizar stock
    p.stock_actual = after

    # 3) insertar kardex
    mov = StockMovement(
        empresa_id=empresa_id,
        producto_id=producto_id,
        tipo=tipo,
        cantidad=cantidad,
        stock_before=before,
        stock_after=after,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        motivo=motivo,
        actor_user_id=actor_user_id,
    )

    db.add(mov)
    return mov

"""