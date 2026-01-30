from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.models import Venta, VentaDetalle, Producto, InventarioMovimiento
from app.services.stock import apply_stock_movement
from app.models.admin_history import AdminHistory

# Funciones para crear ventas y numerar las ventas
def next_sale_number(db: Session, empresa_id: int) -> int:
    stmt = select(func.coalesce(func.max(Venta.numero), 0)).where(Venta.empresa_id == empresa_id)
    return int(db.execute(stmt).scalar_one()) + 1


def create_sale(db: Session, empresa_id: int, user_id: int, payload: dict):
    try:
        numero = next_sale_number(db, empresa_id)

        subtotal = 0.0
        detalles_calc = []

        # 1) Validación + cálculo
        for item in payload["items"]:
            producto_id = int(item["producto_id"])
            qty = float(item["cantidad"])
            desc_item = float(item.get("descuento", 0))

            prod = db.get(Producto, producto_id)
            if not prod or prod.empresa_id != empresa_id or not prod.activo:
                raise ValueError("Producto inválido")

            # IMPORTANTE: aquí validamos contra stock actual REAL
            if float(prod.stock_actual) < qty:
                raise ValueError(f"Stock insuficiente: {prod.nombre}")

            precio = float(prod.precio)
            total_linea = (precio * qty) - desc_item
            if total_linea < 0:
                raise ValueError("Descuento inválido")

            subtotal += total_linea
            detalles_calc.append((prod, qty, precio, desc_item, total_linea))

        descuento_total = float(payload.get("descuento_total", 0))
        total = subtotal - descuento_total
        if total < 0:
            raise ValueError("Descuento total inválido")

        # 2) Crear venta
        venta = Venta(
            empresa_id=empresa_id,
            numero=numero,
            usuario_id=user_id,
            subtotal=subtotal,
            descuento_total=descuento_total,
            total=total,
            metodo_pago=payload.get("metodo_pago", "efectivo"),
            estado="emitida",
            cliente_id=payload.get("cliente_id"),
        )
        db.add(venta)
        db.flush()  # para tener venta.id

        db.add(AdminHistory(
            empresa_id=empresa_id,
            event="sale_issued",
            title=f"Venta emitida: #{venta.numero}",
            message=f"Total S/ {float(venta.total):.2f} • método {venta.metodo_pago}",
            actor_user_id=user_id,
            target_user_id=None,
        ))

        # 3) Detalles + inventario + Kardex (stock_movements)
        for (prod, qty, precio, desc_item, total_linea) in detalles_calc:
            # detalle venta
            vd = VentaDetalle(
                venta_id=venta.id,
                producto_id=prod.id,
                cantidad=qty,
                precio_unitario=precio,
                descuento=desc_item,
                total_linea=total_linea,
            )
            db.add(vd)

            # inventario_movimientos (si lo sigues usando)
            mov = InventarioMovimiento(
                empresa_id=empresa_id,
                producto_id=prod.id,
                tipo="venta",
                cantidad=qty,
                costo_unitario=float(prod.costo),
                referencia=f"VENTA #{numero}",
                created_by=user_id,
            )
            db.add(mov)

            # ✅ Kardex REAL (stock_movements) + stock_actual update (solo aquí)
            # ... creas venta y detalles ...
            #for item in item:
            apply_stock_movement(
                db,
                empresa_id=empresa_id,
                producto_id=prod.id,
                tipo="SALE",
                cantidad=-qty,  # resta stock
                actor_user_id=user_id,
                ref_tipo="venta",
                ref_id=venta.id,
                motivo=f"Venta #{venta.numero}"
            )

        db.commit()
        db.refresh(venta)
        #db.flush()
        return venta

    except Exception:
        db.rollback()
        raise

"""
def create_sale(db: Session, empresa_id: int, user_id: int, payload: dict):
    # Transacción: si algo falla, rollback automático
    with db.begin():
        numero = next_sale_number(db, empresa_id)

        subtotal = 0.0
        detalles = []

        # Validar stock y calcular
        for item in payload["items"]:
            prod = db.get(Producto, item["producto_id"])
            if not prod or prod.empresa_id != empresa_id or not prod.activo:
                raise ValueError("Producto inválido")

            qty = float(item["cantidad"])
            if float(prod.stock_actual) < qty:
                raise ValueError(f"Stock insuficiente: {prod.nombre}")

            precio = float(prod.precio)
            desc = float(item.get("descuento", 0))
            total_linea = (precio * qty) - desc
            if total_linea < 0:
                raise ValueError("Descuento inválido")

            subtotal += total_linea
            detalles.append((prod, qty, precio, desc, total_linea))

        descuento_total = float(payload.get("descuento_total", 0))
        total = subtotal - descuento_total
        if total < 0:
            raise ValueError("Descuento total inválido")

        venta = Venta(
            empresa_id=empresa_id,
            numero=numero,
            usuario_id=user_id,
            subtotal=subtotal,
            descuento_total=descuento_total,
            total=total,
            metodo_pago=payload.get("metodo_pago", "efectivo"),
        )
        db.add(venta)
        db.flush()  # para tener venta.id

        for prod, qty, precio, desc, total_linea in detalles:
            # detalle
            vd = VentaDetalle(
                venta_id=venta.id,
                producto_id=prod.id,
                cantidad=qty,
                precio_unitario=precio,
                descuento=desc,
                total_linea=total_linea,
            )
            db.add(vd)

            

            # movimiento inventario tipo venta
            mov = InventarioMovimiento(
                empresa_id=empresa_id,
                producto_id=prod.id,
                tipo="venta",
                cantidad=qty,
                costo_unitario=float(prod.costo),
                referencia=f"VENTA #{numero}",
                created_by=user_id,
            )
            db.add(mov)

            # descontar stock
            prod.stock_actual = float(prod.stock_actual) - qty

        
        db.flush()
        return venta
"""


# Funciones para listar y leer detalles de las ventas que se vendio
def list_sales(db, empresa_id: int, limit: int = 50):
    stmt = (
        select(Venta)
        .where(Venta.empresa_id == empresa_id)
        .order_by(desc(Venta.fecha))
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()

def get_sale_detail(db, empresa_id: int, sale_id: int):
    venta = db.get(Venta, sale_id)
    if not venta or venta.empresa_id != empresa_id:
        return None

    rows = db.execute(
        select(
            VentaDetalle.producto_id,
            Producto.nombre,
            VentaDetalle.cantidad,
            VentaDetalle.precio_unitario,
            VentaDetalle.descuento,
            VentaDetalle.total_linea,
        )
        .join(Producto, Producto.id == VentaDetalle.producto_id)
        .where(VentaDetalle.venta_id == venta.id)
    ).all()

    items = [
        {
            "producto_id": r[0],
            "nombre": r[1],
            "cantidad": float(r[2]),
            "precio_unitario": float(r[3]),
            "descuento": float(r[4]),
            "total_linea": float(r[5]),
        }
        for r in rows
    ]

    return venta, items


# Funcion para cancelar las ventas de los productos
def cancel_sale(db: Session, empresa_id: int, user_id: int, sale_id: int, motivo: str | None = None):
    try:
        venta = db.get(Venta, sale_id)
        if not venta or venta.empresa_id != empresa_id:
            return None

        if venta.estado == "anulada":
            raise ValueError("La venta ya está anulada")

        detalles = db.execute(
            select(VentaDetalle).where(VentaDetalle.venta_id == venta.id)
        ).scalars().all()


        # ✅ revertir stock con Kardex
        for d in detalles:
            apply_stock_movement(
                db,
                empresa_id=empresa_id,
                producto_id=d.producto_id,
                tipo="CANCEL_SALE",
                cantidad=+float(d.cantidad),  # devuelve stock
                actor_user_id=user_id,
                ref_tipo="venta",
                ref_id=venta.id,
                motivo=f"Anulación venta #{venta.numero}: {motivo or ''}".strip()
            )
        # db.commit()
        
        # 1) marcar venta anulada primero
        venta.estado = "anulada"
        if hasattr(venta, "motivo_anulacion"):
            venta.motivo_anulacion = motivo

        # 3) auditoría
        db.add(AdminHistory(
            empresa_id=empresa_id,
            event="sale_cancelled",
            title=f"Venta anulada: #{venta.numero}",
            message=f"Motivo: {motivo or '—'} • Total S/ {float(venta.total):.2f}",
            actor_user_id=user_id,
            target_user_id=None,
        ))

        db.commit()
        #db.flush()
        db.refresh(venta)
        return venta

    except Exception:
        db.rollback()
        raise

"""
def cancel_sale(db, empresa_id: int, sale_id: int, motivo: str | None = None):
    venta = db.get(Venta, sale_id)
    if not venta or venta.empresa_id != empresa_id:
        return None

    if venta.estado == "anulada":
        raise ValueError("La venta ya está anulada")

    # traer detalle
    detalles = db.execute(
        select(VentaDetalle).where(VentaDetalle.venta_id == venta.id)
    ).scalars().all()

    # devolver stock
    for d in detalles:
        prod = db.get(Producto, d.producto_id)
        if prod and prod.empresa_id == empresa_id:
            prod.stock_actual = float(prod.stock_actual) + float(d.cantidad)

    # marcar venta como anulada
    venta.estado = "anulada"
    # si tu modelo tiene campo motivo, úsalo:
    if hasattr(venta, "motivo_anulacion"):
        venta.motivo_anulacion = motivo


    db.refresh(venta)
    return venta
"""






