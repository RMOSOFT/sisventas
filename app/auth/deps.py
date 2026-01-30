from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.deps import get_db
from app.models.usuario import Usuario


# Funcion para el login del admin y su vendedor panel login
# Funciones para dependencias del login cuado expira tokens o no hay cookies
def get_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(settings.COOKIE_NAME_ADMIN)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY_JWT_ADMIN, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        request.state.sid = payload.get("sid")  # ✅ GUARDAMOS SID AQUÍ
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.execute(select(Usuario).where(Usuario.id == user_id, Usuario.activo == True)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no existe o inactivo")

    return user

# Agregar sid al JWT función para leer sid
def get_session_id(request: Request) -> str | None:
    token = get_token_from_cookie(request)
    if not token:
        raise HTTPException(401, "No autenticado")
        #return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY_JWT_ADMIN, algorithms=[settings.ALGORITHM])
        sid = payload.get("sid")
        return sid if isinstance(sid, str) else None
    except JWTError:
        raise HTTPException(401, "Token inválido")
        #return None



def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    return user
