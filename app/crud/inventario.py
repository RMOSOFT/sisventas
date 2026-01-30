from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import InventarioMovimiento, Producto

def create_movement(db: Session, empresa_id: int, user_id: int | None, data):
    prod = db.get(Producto, data["producto_id"])
    if not prod or prod.empresa_id != empresa_id:
        raise ValueError("Producto no existe")

    tipo = data["tipo"]
    qty = data["cantidad"]

    if tipo == "entrada":
        prod.stock_actual = float(prod.stock_actual) + qty
    elif tipo == "salida":
        if float(prod.stock_actual) < qty:
            raise ValueError("Stock insuficiente")
        prod.stock_actual = float(prod.stock_actual) - qty
    elif tipo == "ajuste":
        prod.stock_actual = qty
    else:
        raise ValueError("Tipo inválido")

    mov = InventarioMovimiento(
        empresa_id=empresa_id,
        producto_id=prod.id,
        tipo=tipo,
        cantidad=qty,
        costo_unitario=data.get("costo_unitario"),
        referencia=data.get("referencia"),
        created_by=user_id,
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov

def low_stock(db: Session, empresa_id: int):
    stmt = select(Producto).where(
        Producto.empresa_id == empresa_id,
        Producto.activo == True,
        Producto.stock_actual <= Producto.stock_minimo
    )
    return db.execute(stmt).scalars().all()