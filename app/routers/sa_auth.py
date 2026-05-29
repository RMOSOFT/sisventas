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

router = APIRouter(prefix="/api/v1/superadmin/auth", tags=["sa_auth"])
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