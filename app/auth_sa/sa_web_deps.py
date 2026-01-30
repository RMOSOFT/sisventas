from fastapi import Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.auth_sa.sa_deps import get_current_superadmin  # tu lógica API
# (sa_get_current_user = la función que valida cookie y devuelve superadmin)

def web_current_superadmin(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        return get_current_superadmin(request=request, db=db)
    except Exception:
        # si no está autenticado => redirige al login superadmin
        return RedirectResponse(url="/superadmin/login", status_code=302)