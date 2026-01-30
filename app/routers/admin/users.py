from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.context import CryptContext
from app.core.deps import get_db
from app.auth.deps import require_admin
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut
import secrets
from datetime import datetime, timedelta, timezone
from app.services.email_service import send_email
from app.core.config import settings
from app.auth.deps import get_current_user
from app.auth.web_deps import web_context

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Funciones de Router Admin: “Empleados” (crear usuario y enviar link)
router = APIRouter(prefix="/users", tags=["admin_users"])

def build_set_password_email(nombre: str, empresa: str, link: str) -> str:
    # HTML simple pero pro (compatible Gmail)
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:16px">
      <div style="padding:14px 16px;border-radius:14px;background:#0b1220;color:#fff">
        <div style="font-weight:800;font-size:20px;letter-spacing:.3px">RMOSOFT</div>
        <div style="color:#9bb1d1;font-size:13px;margin-top:4px">Acceso al sistema de ventas</div>
      </div>

      <div style="padding:18px 2px">
        <h2 style="margin:0 0 10px 0;color:#0b1220">Crea tu contraseña</h2>
        <p style="margin:0 0 10px 0;color:#334155;line-height:1.5">
          Hola <b>{nombre}</b>, te han creado un acceso para la empresa <b>{empresa}</b>.
          Para activar tu cuenta, crea tu contraseña usando el siguiente botón:
        </p>

        <div style="margin:16px 0">
          <a href="{link}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;
             padding:12px 16px;border-radius:10px;font-weight:700">
            Crear contraseña
          </a>
        </div>

        <p style="margin:0;color:#64748b;font-size:13px;line-height:1.5">
          Este enlace vence en 30 minutos. Si no solicitaste esto, ignora el mensaje.
        </p>

        <p style="margin:14px 0 0 0;color:#94a3b8;font-size:12px">
          © RMOSOFT
        </p>
      </div>
    </div>
    """

@router.get("")
def list_users(db: Session = Depends(get_db), admin=Depends(get_current_user)):
    empresa_id = admin.empresa_id
    rows = db.execute(
        select(Usuario).where(Usuario.empresa_id == empresa_id).order_by(Usuario.id.asc())
    ).scalars().all()

    return [{
        "id": u.id,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "email": u.email,
        "username": getattr(u, "username", None),
        "telefono": u.telefono,
        "rol": u.rol,
        "activo": u.activo,
        "last_login_at": str(u.last_login_at) if u.last_login_at else None
    } for u in rows]

@router.post("")
def create_user(payload: dict, db: Session = Depends(get_db), admin=Depends(require_admin)):
    empresa_id = admin.empresa_id

    nombre = (payload.get("nombre") or "").strip()
    apellido = (payload.get("apellido") or "").strip() or None
    email = (payload.get("email") or "").strip().lower()
    username = (payload.get("username") or "").strip().lower() or None
    telefono = (payload.get("telefono") or "").strip() or None
    rol = (payload.get("rol") or "vendedor").strip().lower()

    if not nombre or not email:
        raise HTTPException(400, "Nombre y email son requeridos")

    if rol not in ("admin", "vendedor"):
        raise HTTPException(400, "Rol inválido")

    # duplicados por empresa
    if db.execute(select(Usuario).where(Usuario.empresa_id == empresa_id, Usuario.email == email)).scalar_one_or_none():
        raise HTTPException(400, "Ese email ya existe en tu empresa")

    if username:
        if db.execute(select(Usuario).where(Usuario.empresa_id == empresa_id, Usuario.username == username)).scalar_one_or_none():
            raise HTTPException(400, "Ese username ya existe en tu empresa")

    # token para crear contraseña
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    u = Usuario(
        empresa_id=empresa_id,
        nombre=nombre,
        apellido=apellido,
        email=email,
        password_hash="pending",  # placeholder; se reemplaza cuando cree contraseña
        rol=rol,
        activo=True,
        telefono=telefono,
    )
    if hasattr(u, "username"):
        u.username = username

    # campos reset
    u.reset_token = token
    u.reset_token_expires_at = expires

    db.add(u)
    db.commit()
    db.refresh(u)

    # link absoluto
    base_url = getattr(settings, "PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    link = f"{base_url}/admin/reset?token={token}"

    empresa_nombre = "Tu empresa"
    try:
        # si tienes relación Empresa la puedes usar; si no, déjalo fijo
        empresa_nombre = "Empresa ID " + str(empresa_id)
    except Exception:
        pass

    html = build_set_password_email(nombre=u.nombre, empresa=empresa_nombre, link=link)
    send_email(u.email, "RMOSOFT • Crea tu contraseña", html)

    return {"ok": True, "id": u.id}



@router.get("", response_model=list[UsuarioOut])
def list_users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    # empresa del admin (luego sacas empresa_id del token)
    empresa_id = admin.empresa_id
    rows = db.execute(select(Usuario).where(Usuario.empresa_id == empresa_id).order_by(Usuario.id.asc())).scalars().all()
    return rows

@router.post("", response_model=UsuarioOut)
def create_user(payload: UsuarioCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    empresa_id = admin.empresa_id

    email = payload.email.strip().lower()
    username = (payload.username or "").strip().lower() or None

    # validar duplicados
    q = select(Usuario).where(Usuario.empresa_id == empresa_id, Usuario.email == email)
    if db.execute(q).scalar_one_or_none():
        raise HTTPException(400, "Ese email ya existe en tu empresa")

    if username:
        q2 = select(Usuario).where(Usuario.empresa_id == empresa_id, Usuario.username == username)
        if db.execute(q2).scalar_one_or_none():
            raise HTTPException(400, "Ese username ya existe en tu empresa")

    # password temporal (PRO)
    temp_pass = "Emp-" + secrets.token_urlsafe(8)
    ph = pwd.hash(temp_pass)

    u = Usuario(
        empresa_id=empresa_id,
        nombre=payload.nombre.strip(),
        apellido=(payload.apellido.strip() if payload.apellido else None),
        email=email,
        username=username,
        telefono=(payload.telefono.strip() if payload.telefono else None),
        rol=payload.rol,
        activo=True,
        password_hash=ph,
    )

    token = secrets.token_urlsafe(32)
    u.reset_token = token
    u.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    db.add(u)
    db.commit()
    db.refresh(u)

    # Opcional: enviar correo con temp_pass o con link reset
    # >>> mejor: link reset (más pro) <<<
    # generate reset_token + expires y enviar correo

    return u

# filtros por nombre real (no por ID), con dropdown
@router.get("/min")
def users_min(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    stmt = select(Usuario).where(
        Usuario.empresa_id == admin.empresa_id,
        Usuario.activo == True
    ).order_by(Usuario.nombre.asc())

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            (Usuario.nombre.ilike(like)) |
            (Usuario.apellido.ilike(like)) |
            (Usuario.email.ilike(like)) |
            (Usuario.rol.ilike(like))
        )

    users = db.execute(stmt.limit(50)).scalars().all()

    return [{
        "id": u.id,
        "nombre": u.nombre,
        "apellido": u.apellido,
        "rol": u.rol,
        "email": u.email,
    } for u in users]