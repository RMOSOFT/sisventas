from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import get_db
from app.models.super_admin import SuperAdmin

# Funcion para el login del superadmin panel login
# Funciones para dependencias del login cuado expira tokens o no hay cookies
def get_sa_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(settings.COOKIE_NAME_SA)

def get_current_superadmin(
    request: Request,
    db: Session = Depends(get_db),
) -> SuperAdmin:
    token = get_sa_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY_JWT_SA, algorithms=[settings.ALGORITHM])
        sa_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")

    sa = db.execute(
        select(SuperAdmin).where(SuperAdmin.id == sa_id, SuperAdmin.activo == True)
    ).scalar_one_or_none()

    if not sa:
        raise HTTPException(status_code=401, detail="SuperAdmin no existe o inactivo")

    return sa