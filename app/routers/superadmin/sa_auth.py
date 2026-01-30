from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.config import settings
from app.core.deps import get_db
from app.models.super_admin import SuperAdmin

from sqlalchemy import select, or_

from datetime import datetime, timedelta, timezone
import secrets
import hashlib
from app.services.email_service import send_email

#router = APIRouter(prefix="/api/v1/superadmin/auth", tags=["sa_auth"])
router = APIRouter(prefix="/auth", tags=["superadmin_auth"])

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(sub: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": exp}
    return jwt.encode(payload, settings.SECRET_KEY_JWT_SA, algorithm=settings.ALGORITHM)

@router.post("/login")
def login(data: dict, response: Response, db: Session = Depends(get_db)):
    user = (data.get("user") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not user or not password:
        raise HTTPException(status_code=400, detail="Usuario/email y password requeridos")

    user_l = user.lower()

    sa_user = db.execute(
        select(SuperAdmin).where(
            or_(
                func.lower(SuperAdmin.email) == user_l,
                func.lower(SuperAdmin.username) == user_l,
            )
        )
    ).scalar_one_or_none()

    if not sa_user or not sa_user.activo:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not pwd.verify(password, sa_user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    sa_user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_token(str(sa_user.id))
    response.set_cookie(
        key=settings.COOKIE_NAME_SA,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"ok": True}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.COOKIE_NAME_SA, path="/")
    return {"ok": True}


# Funcion para recuperar contraseña
@router.post("/forgot")
def forgot(data: dict, db: Session = Depends(get_db)):
    user = (data.get("user") or data.get("email") or "").strip().lower()

    # Respuesta genérica (seguridad)
    ok_msg = {"ok": True, "message": "Si el usuario existe, te enviamos un enlace de recuperación."}

    if not user:
        return ok_msg

    sa = db.execute(
        select(SuperAdmin).where(
            (SuperAdmin.email == user) | (SuperAdmin.username == user)
        )
    ).scalar_one_or_none()

    if not sa or not sa.activo:
        return ok_msg

    # token real (solo se manda por correo)
    raw_token = secrets.token_urlsafe(32)

    # guardamos HASH del token (mejor seguridad)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    sa.reset_token = token_hash
    sa.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.SA_RESET_EXPIRE_MINUTES)
    db.commit()

    link = f"{settings.FRONTEND_BASE_URL}/superadmin/reset?token={raw_token}"

    html = f"""
    <div style="font-family:Arial,sans-serif">
      <h2>RMOSOFT - Recuperar contraseña</h2>
      <p>Hola <b>{sa.nombre}</b>,</p>
      <p>Haz clic en este enlace para crear una nueva contraseña (vence en {settings.SA_RESET_EXPIRE_MINUTES} min):</p>
      <p><a href="{link}">{link}</a></p>
      <p>Si no fuiste tú, ignora este correo.</p>
    </div>
    """

    send_email(sa.email, "RMOSOFT • Recuperar contraseña (SuperAdmin)", html)
    return ok_msg

# Funcion para rellenar los nuevos campos de la contraseña
@router.post("/reset")
def reset_password(data: dict, db: Session = Depends(get_db)):
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Token y nueva contraseña requeridos (mín 8).")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    sa = db.execute(
        select(SuperAdmin).where(SuperAdmin.reset_token == token_hash)
    ).scalar_one_or_none()

    if not sa or not sa.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="Token inválido o vencido.")

    if datetime.now(timezone.utc) > sa.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="Token vencido. Vuelve a pedir recuperación.")

    sa.password_hash = pwd.hash(new_password)
    sa.reset_token = None
    sa.reset_token_expires_at = None
    db.commit()

    return {"ok": True}