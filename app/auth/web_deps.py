from fastapi import Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.models.empresa import Empresa


# Funcion para sacar el nombre de la empresa en el templates sesión o redirect + (user + empresa)
def web_context(request: Request, db: Session = Depends(get_db)):
    """
    Retorna (user, empresa) o un RedirectResponse si no está autenticado.
    """
    try:
        user = get_current_user(request=request, db=db)
    except Exception:
        return RedirectResponse(url="/admin/login?expired=1", status_code=302)
        #return RedirectResponse(url="/admin/login", status_code=302)

    empresa = db.execute(
        select(Empresa).where(Empresa.id == user.empresa_id)
    ).scalar_one_or_none()

    return {"user": user, "empresa": empresa}


# Funcion para redirigir segun el login admin o vendedor
def web_require_admin(ctx = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    if ctx["user"].rol != "admin":
        return RedirectResponse(url="/admin/pos?no_access=1", status_code=302)
    return ctx

# (Opcional) si todavía quieres web_current_user:
def web_current_user(ctx = Depends(web_context)):
    if isinstance(ctx, RedirectResponse):
        return ctx
    return ctx["user"]