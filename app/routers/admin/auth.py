from fastapi import APIRouter, Depends, Form, Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, or_
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timezone
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from app.core.deps import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.models.usuario import Usuario
from app.core.security import verify_password  # tu función passlib
from app.services.email_service import send_email



#router = APIRouter(tags=["auth"])
#router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
router = APIRouter(prefix="/auth", tags=["ad_auth"])
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")



# Funcion para el login para validar credenciales por username o email
@router.post("/login")
def login(data: dict, response: Response, db: Session = Depends(get_db)):
    user = (data.get("user") or data.get("email") or "").strip()
    #email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not user or not password:
        raise HTTPException(status_code=400, detail="Usuario/email y password requeridos")

    user_l = user.lower()
    user = db.execute(
        select(Usuario).where(
            Usuario.activo == True,
            or_(Usuario.email == user_l, Usuario.username == user_l)
        )
    ).scalar_one_or_none()

    #user = db.execute(select(Usuario).where(Usuario.email == email, Usuario.activo == True)).scalar_one_or_none()
    
    if not user or not pwd.verify(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    sid = secrets.token_hex(16)  # 32 chars (OK)
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode({"sub": str(user.id), "sid": sid, "exp": exp}, settings.SECRET_KEY_JWT_ADMIN, algorithm=settings.ALGORITHM)

    response.set_cookie(
        key=settings.COOKIE_NAME_ADMIN,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # en producción True con HTTPS
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"ok": True, "rol": user.rol, "nombre": user.nombre}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.COOKIE_NAME_ADMIN)
    return {"ok": True}

# Funcion con html de recuperacion presentable
def build_reset_email(nombre: str, link: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:16px">
      <div style="padding:14px 16px;border-radius:14px;background:#0f172a;color:#fff">
        <div style="font-weight:800;font-size:20px">RMOSOFT</div>
        <div style="color:#93c5fd;font-size:13px;margin-top:4px">Recuperación de contraseña</div>
      </div>

      <div style="padding:18px 2px">
        <h2 style="margin:0 0 10px 0;color:#0f172a">Restablecer contraseña</h2>
        <p style="margin:0 0 10px 0;color:#334155;line-height:1.5">
          Hola <b>{nombre}</b>. Recibimos una solicitud para restablecer tu contraseña.
        </p>

        <div style="margin:16px 0">
          <a href="{link}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;
             padding:12px 16px;border-radius:10px;font-weight:700">
            Restablecer contraseña
          </a>
        </div>

        <p style="margin:0;color:#64748b;font-size:13px;line-height:1.5">
          Este enlace vence en 30 minutos. Si no fuiste tú, ignora este correo.
        </p>
      </div>
    </div>
    """

# Funcion para el campos si olvido el usuario su contraseña
@router.post("/forgot")
def forgot(data: dict, db: Session = Depends(get_db)):
    user_raw = (data.get("user") or data.get("email") or "").strip().lower()
    if not user_raw:
        raise HTTPException(400, "Usuario/email requerido")

    u = db.execute(
        select(Usuario).where(
            Usuario.activo == True,
            or_(
                Usuario.email == user_raw,
                Usuario.username == user_raw if hasattr(Usuario, "username") else False
            )
        )
    ).scalar_one_or_none()

    # por seguridad: no reveles si existe o no
    if not u:
        return {"ok": True}

    token = secrets.token_urlsafe(32)
    u.reset_token = token
    u.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()

    base_url = getattr(settings, "PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    link = f"{base_url}/admin/reset?token={token}"

    html = build_reset_email(u.nombre, link)
    send_email(u.email, "RMOSOFT • Recuperar contraseña", html)

    return {"ok": True}

# Funcion para Endpoint reset (crear contraseña o reset normal)
@router.post("/reset")
def reset_password(data: dict, db: Session = Depends(get_db)):
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Token y nueva contraseña requeridos")

    u = db.execute(
        select(Usuario).where(
            Usuario.reset_token == token,
            Usuario.reset_token_expires_at.isnot(None),
            Usuario.reset_token_expires_at > datetime.now(timezone.utc),
            Usuario.activo == True
        )
    ).scalar_one_or_none()

    if not u:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    u.password_hash = pwd.hash(new_password)
    u.reset_token = None
    u.reset_token_expires_at = None
    db.commit()

    return {"ok": True}

