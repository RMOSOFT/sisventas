from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.models import Venta, VentaDetalle, Producto, InventarioMovimiento, Cliente
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

        metodo = (payload.get("metodo_pago") or "efectivo").lower()

        efectivo_recibido = float(payload.get("efectivo_recibido") or 0)
        vuelto = 0.0

        if metodo != "efectivo":
            efectivo_recibido = 0.0
            vuelto = 0.0
            
        else:
            if efectivo_recibido < total:
                raise ValueError("Efectivo insuficiente para completar la venta")
            vuelto = max(efectivo_recibido - total, 0.0)


        # Elegir tipo/serie según cliente (DNI vs RUC)
        cliente_id = payload.get("cliente_id")

        tipo_comprobante = "B"
        serie = "B001"

        if cliente_id:
            cli = db.get(Cliente, int(cliente_id))
            if cli and cli.empresa_id == empresa_id:
                tipo_doc = (cli.tipo_doc or "").upper().strip()
                # Si es RUC => FACTURA
                if tipo_doc == "RUC":
                    tipo_comprobante = "F"
                    serie = "F001"


        # Calculamos correlativo
        correlativo = next_correlativo_by_serie(db, empresa_id, serie)

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

            efectivo_recibido=efectivo_recibido,
            vuelto=vuelto,

            tipo_comprobante=tipo_comprobante,
            serie=serie,
            correlativo=correlativo,
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
            VentaDetalle.producto_id,     # r[0]
            Producto.nombre,              # r[1]
            Producto.marca,               # r[2]
            Producto.unidad,              # r[3]
            VentaDetalle.cantidad,        # r[4]
            VentaDetalle.precio_unitario, # r[5]
            VentaDetalle.descuento,       # r[6]
            VentaDetalle.total_linea,     # r[7]
        )
        .join(Producto, Producto.id == VentaDetalle.producto_id)
        .where(VentaDetalle.venta_id == venta.id)
    ).all()

    items = [
        {
            "producto_id": r[0],           
            "nombre": r[1],
            "marca": r[2] or "",
            "unidad": r[3] or "UND",        
            "cantidad": float(r[4] or 0),        #3
            "precio_unitario": float(r[5] or 0), #3
            "descuento": float(r[6]),       #4
            "total_linea": float(r[7]),     #5
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


# generar correlativo separado por serie.
def next_correlativo_by_serie(db, empresa_id: int, serie: str) -> int:
    last = db.execute(
        select(func.max(Venta.correlativo))
        .where(Venta.empresa_id == empresa_id, Venta.serie == serie)
    ).scalar()

    return int(last or 0) + 1





