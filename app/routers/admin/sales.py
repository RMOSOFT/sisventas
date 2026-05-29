from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.schemas.venta import VentaCreate, VentaOut, VentaListOut, VentaDetailOut, VentaCancelIn
from app.crud import venta as crud
from app.models import Usuario, Empresa
from app.models import Cliente

import base64
from io import BytesIO
# (Opcional) QR:
import qrcode
# (Recomendado) letras:
from num2words import num2words

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
        "metodo_pago": v.metodo_pago,
        "efectivo_recibido": float(getattr(v, "efectivo_recibido", 0) or 0),
        "vuelto": float(getattr(v, "vuelto", 0) or 0),
        "can_cancel": True if user.rol == "admin" else True,

        "tipo_comprobante": getattr(v, "tipo_comprobante", "B"),
        "serie": getattr(v, "serie", "B001"),
        "correlativo": int(getattr(v, "correlativo", 0) or 0),
        "comprobante": f"{getattr(v,'serie','B001')}-{int(getattr(v,'correlativo',0) or 0):06d}",

    }


# Funcion mejorada para listar las ventas
@router.get("", response_model=list[VentaListOut])
def list_sales(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.list_sales(db, user.empresa_id, limit)


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
        "efectivo_recibido": float(venta.efectivo_recibido or 0),
        "vuelto": float(venta.vuelto or 0),
        "can_cancel": True,
    }


# Funcion para traducir de numeros soles a letras soles
def total_a_letras_soles(total: float) -> str:
    # 26.00 -> "VEINTISEIS Y 00/100 SOLES"
    entero = int(total)
    cent = int(round((total - entero) * 100))
    letras = num2words(entero, lang="es").upper()
    letras = letras.replace("VEINTIUNO", "VEINTIUN")  # opcional estilo boleta
    return f"{letras} Y {cent:02d}/100 SOLES"

# Funcion de endpoint para ver que salga la pagina de los tickets de ventas
@router.get("/{sale_id}/ticket", response_class=HTMLResponse)
def sale_ticket(
    sale_id: int, 
    request: Request, 
    db: Session = Depends(get_db), 
    user: Usuario = Depends(get_current_user),
):

    res = crud.get_sale_detail(db, user.empresa_id, sale_id)
    if not res:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    venta, items = res # items viene del CRUD (dicts)

    # DEBUG (solo para ver qué llega)
    if items:
        print("DEBUG ITEM 0:", items[0], type(items[0]))

    # =========================
    # EMPRESA
    # =========================
    empresa = db.get(Empresa, user.empresa_id)
    empresa_nombre = empresa.nombre if empresa else "Empresa"

    empresa_ruc = getattr(empresa, "ruc", None) if empresa else None
    empresa_direccion = getattr(empresa, "direccion", None) if empresa else None
    empresa_telefono = getattr(empresa, "telefono", None) if empresa else None
    empresa_email = getattr(empresa, "email", None) if empresa else None
    empresa_web = getattr(empresa, "web", None) if empresa else None


    # =========================
    # CLIENTE por cliente_id (si tu venta guarda cliente_id, aquí lo obtienes)
    # =========================
    cliente_nombre = ""
    cliente_doc = ""
    cliente_direccion = ""

    cli = None
    if getattr(venta, "cliente_id", None):
        cli = db.get(Cliente, venta.cliente_id)
        if cli and getattr(cli, "empresa_id", None) != user.empresa_id:
            cli = None

    if cli:
        cliente_nombre = (getattr(cli, "razon_social", None) or getattr(cli, "nombres", None) or "").strip() or None
        tipo = (getattr(cli, "tipo_doc", "") or "").strip()
        num = (getattr(cli, "num_doc", "") or "").strip()
        cliente_doc = f"{tipo}: {num}".strip() if (tipo or num) else None
        cliente_direccion = (getattr(cli, "direccion", "") or "").strip() or None

    # =========================
    # TIPO COMPROBANTE + SERIE
    # =========================
    #tipo_comprobante = "BOLETA DE VENTA ELECTRÓNICA"
    #serie = "B001"

    # Si es RUC => factura
    #if cli and (getattr(cli, "tipo_doc", "") or "").upper() == "RUC":
    #    tipo_comprobante = "FACTURA ELECTRÓNICA"
    #    serie = "F001"

    # Correlativo con ceros
    #correlativo = str(venta.numero).zfill(6)
    #comprobante_num = f"{serie}-{correlativo}"



    # =========================
    # ITEMS normalizados para el templates
    # =========================
    items_norm = []
    for it in items:
        cantidad = float(it.get("cantidad") or 0)
        precio = float(it.get("precio_unitario") or 0)
        descuento = float(it.get("descuento") or 0)
        total_linea = float(it.get("total_linea") or ((cantidad * precio) - descuento))
        

        items_norm.append({
            "cantidad": cantidad,
            "unidad": it.get("unidad") or "UND",
            "descripcion": it.get("nombre") or "",
            "marca": it.get("marca") or "",
            "punit": precio,
            "total": total_linea,
            "descuento": descuento,
        })

    # Nro de ítems (como boleta: cantidad de líneas)
    n_items = len(items_norm)

    # =========================
    # TOTALES
    # =========================
    subtotal = float(venta.subtotal or 0) 
    descuento_total = float(venta.descuento_total or 0)
    total = float(venta.total or 0)
    icbper = float(getattr(venta, "icbper", 0) or 0)  # si no existe, 0
    # =========================
    # CAJA / CAJERO / PAGO
    # =========================
    caja = getattr(venta, "caja", None) or "CAJA 1"
    cajero = getattr(user, "nombre", None) or getattr(user, "email", None) or "CAJERO"

    forma_pago = (venta.metodo_pago or "EFECTIVO").upper()

    # Efectivo / Vuelto (si tu venta ya guarda efectivo_recibido)
    efectivo = float(getattr(venta, "efectivo_recibido", 0) or 0)
    vuelto = float(getattr(venta, "vuelto", 0) or 0)

    if (venta.metodo_pago or "").lower() == "efectivo":
        vuelto = max(efectivo - total, 0.0)
    else:
        efectivo = 0.0
        vuelto = 0.0
    

    # =========================
    # SON (TOTAL EN LETRAS)
    # =========================
    son = total_a_letras_soles(total)

    # =========================
    # QR (opcional)
    # =========================
    # Ejemplo de data para QR (puedes poner tu URL real)
    # Aqui podemos cambiar segun nuestra url con ngrok
    base_url = str(request.base_url).rstrip("/")
    qr_data_url = f"{base_url}/api/v1/admin/sales/{venta.id}/ticket"
    #qr_data_url = f"http://127.0.0.1:8000/api/v1/admin/sales/{venta.id}/ticket"

    qr = qrcode.QRCode(box_size=2, border=1)
    qr.add_data(qr_data_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    resolucion = "0920050000036"
    legal_fecha = venta.fecha.strftime("%d/%m/%Y")
    web_consulta = (empresa_web or "www.rmosoft.pe/consulta")

    # =========================
    # COMPROBANTE (desde la venta)
    # =========================
    # BOLETA o FACTURA y número serie-correlativo
    tipo = (getattr(venta, "tipo_comprobante", "B") or "B").upper()
    serie_doc = getattr(venta, "serie", "B001") or "B001"
    corr = int(getattr(venta, "correlativo", venta.numero) or venta.numero)
    #comprobante_num = f"{serie}-{corr:06d}"

    doc_titulo = "BOLETA DE VENTA ELECTRÓNICA" if tipo == "B" else "FACTURA ELECTRÓNICA"
    doc_numero = f"{serie_doc}-{corr:08d}"

    print("DEBUG COMPROBANTE:", tipo, serie_doc, corr, doc_titulo, doc_numero)

    return templates.TemplateResponse(
        "admin/ticket_80mm.html",
        {
            "request": request,

            # Tipos de boletas de comprobantes
            # "tipo_comprobante": tipo_comprobante,
            # "comprobante_num": comprobante_num,

            # Empresa (estos son los que tu template espera)
            "empresa_nombre": empresa_nombre,
            "empresa_direccion": empresa_direccion,
            "empresa_telefono": empresa_telefono,
            "empresa_ruc": empresa_ruc,
            "empresa_email": empresa_email,
            "empresa_web": empresa_web,

            # Venta
            "numero": venta.numero,
            "fecha": venta.fecha.strftime("%d/%m/%Y %H:%M:%S"),
            "forma_pago": forma_pago,

            # Cliente
            "cliente_nombre": cliente_nombre,
            "cliente_doc": cliente_doc,
            "cliente_direccion": cliente_direccion,

            # Caja/cajero / Forma pago (NOMBRES EXACTOS)
            "caja": caja,
            "cajero": cajero,

            # Tabla items
            "items": items_norm,
            "n_items": n_items,

            # Totales
            "subtotal": subtotal,
            "descuento_total": descuento_total,
            "icbper": icbper,
            "total": total,

            # Efectivo/vuelto
            "efectivo": efectivo,
            "vuelto": vuelto,

            # Son
            "son": son,

            # QR
            "qr_b64": qr_b64,
            "qr_data_url": qr_data_url,

            # Legal demo
            "resolucion": resolucion,
            "legal_fecha": legal_fecha,
            "web_consulta": web_consulta,

            # Para facturacion o boleta
            "doc_titulo": doc_titulo,
            "doc_numero": doc_numero,
            "tipo_comprobante": tipo,
            "serie": serie_doc,
            "correlativo": corr,
        }
    )


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




