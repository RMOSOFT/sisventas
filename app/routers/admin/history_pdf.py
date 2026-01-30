import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, or_
from app.core.deps import get_db
from app.auth.deps import require_admin
from app.models.usuario import Usuario
from app.models.admin_history import AdminHistory
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

router = APIRouter(prefix="/history", tags=["admin_history_pdf"])

RMOSOFT_BLUE = colors.HexColor("#0B1F3A")  # azul oscuro pro


EVENT_LABELS = {
    "access_request": "Solicitud de acceso",
    "access_approved": "Acceso aprobado",
    "access_denied": "Acceso denegado",
}

EVENT_DOT = {
    "access_request": colors.HexColor("#FBBF24"),  # amarillo
    "access_approved": colors.HexColor("#22C55E"), # verde
    "access_denied": colors.HexColor("#EF4444"),   # rojo
}
#logo_path = "app/web/static/img/logo-rmosoft.png"
#if os.path.exists(logo_path):
    #c.drawImage(ImageReader(logo_path), 1.5*cm, h-2.0*cm, width=2.2*cm, height=2.2*cm, mask='auto')

def _history_query(db, empresa_id, q=None, actor_id=None, target_id=None, event=None, limit=500):
    Actor = aliased(Usuario)
    Target = aliased(Usuario)

    stmt = (
        select(
            AdminHistory,
            Actor.nombre.label("actor_nombre"),
            Actor.apellido.label("actor_apellido"),
            Target.nombre.label("target_nombre"),
            Target.apellido.label("target_apellido"),
        )
        .outerjoin(Actor, Actor.id == AdminHistory.actor_user_id)
        .outerjoin(Target, Target.id == AdminHistory.target_user_id)
        .where(AdminHistory.empresa_id == empresa_id)
        .order_by(AdminHistory.id.desc())
        .limit(limit)
    )

    if event:
        stmt = stmt.where(AdminHistory.event == event)
    if actor_id:
        stmt = stmt.where(AdminHistory.actor_user_id == actor_id)
    if target_id:
        stmt = stmt.where(AdminHistory.target_user_id == target_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(
            AdminHistory.title.ilike(like),
            AdminHistory.message.ilike(like),
            AdminHistory.event.ilike(like),
        ))

    return db.execute(stmt).all()

@router.get("/pdf")
def export_history_pdf(
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),

    q: str | None = Query(default=None),
    actor_id: int | None = Query(default=None),
    target_id: int | None = Query(default=None),
    event: str | None = Query(default=None),
):
    rows = _history_query(db, admin.empresa_id, q=q, actor_id=actor_id, target_id=target_id, event=event)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Header
    c.setFillColor(RMOSOFT_BLUE)
    c.rect(0, h-2.2*cm, w, 2.2*cm, stroke=0, fill=1)

    # Logo (si existe)
    logo_path = "app/web/static/img/logo-rmosoft.png"  # <-- ajusta a tu ruta real
    if os.path.exists(logo_path):
        c.drawImage(
            ImageReader(logo_path),
            1.2*cm, h-2.05*cm,
            width=1.6*cm, height=1.6*cm,
            mask="auto"
        )
        title_x = 3.2*cm
    else:
        title_x = 2*cm


    

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(title_x, h-1.3*cm, "RMOSOFT • Historial de Auditoría")
    #c.drawString(2*cm, h-1.3*cm, "RMOSOFT • Historial de Auditoría")

    c.setFont("Helvetica", 9)
    c.drawString(title_x, h-1.85*cm, f"Empresa ID: {admin.empresa_id}   |   Generado por: {admin.nombre} {admin.apellido}")
    #c.drawString(2*cm, h-1.85*cm, f"Empresa ID: {admin.empresa_id}   |   Generado por: {admin.nombre} {admin.apellido}")

    

    # Table layout
    y = h - 3.2*cm
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Fecha")
    c.drawString(6.2*cm, y, "Evento")
    c.drawString(9.5*cm, y, "Actor")
    c.drawString(13.0*cm, y, "Target")
    c.drawString(16.5*cm, y, "Título")
    y -= 0.6*cm

    c.setStrokeColor(colors.lightgrey)
    c.line(2*cm, y, w-2*cm, y)
    y -= 0.3*cm

    c.setFont("Helvetica", 9)

    for i, (hrow, a_nom, a_ape, t_nom, t_ape) in enumerate(rows):
        if y < 2.2*cm:
            c.showPage()
            y = h - 2.5*cm
            c.setFont("Helvetica", 9)

        # zebra
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#F5F7FB"))
            c.rect(1.8*cm, y-0.25*cm, w-3.6*cm, 0.6*cm, stroke=0, fill=1)

        c.setFillColor(colors.black)

        fecha = str(hrow.created_at)[:19].replace("T", " ")
        actor = (f"{a_nom or ''} {a_ape or ''}").strip() or (f"#{hrow.actor_user_id}" if hrow.actor_user_id else "—")
        target = (f"{t_nom or ''} {t_ape or ''}").strip() or (f"#{hrow.target_user_id}" if hrow.target_user_id else "—")
        titulo = (hrow.title or "")[:22]  # corto para que no rompa

        c.drawString(2*cm, y, fecha)

        ev = hrow.event or ""
        ev_label = EVENT_LABELS.get(ev, ev)

        # puntito de color
        c.setFillColor(EVENT_DOT.get(ev, colors.grey))
        c.circle(6.15*cm, y+0.15*cm, 0.12*cm, stroke=0, fill=1)

        c.setFillColor(colors.black)
        c.drawString(6.35*cm, y, ev_label[:18])
        #c.drawString(6.2*cm, y, (hrow.event or "")[:16])
        
        c.drawString(9.5*cm, y, actor[:18])
        c.drawString(13.0*cm, y, target[:18])
        c.drawString(16.5*cm, y, titulo)

        y -= 0.65*cm

    c.showPage()
    c.save()
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=historial_rmosoft.pdf"}
    )