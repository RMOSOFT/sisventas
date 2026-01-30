from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.deps import get_db
from app.auth_sa.sa_deps import get_current_superadmin
from app.models import Empresa
from app.models.super_admin import SuperAdmin

#router = APIRouter(prefix="/api/v1/superadmin/empresas", tags=["sa_empresas"])
router = APIRouter(prefix="/empresas", tags=["sa_empresas"])

@router.get("/")
def list_empresas(
    db: Session = Depends(get_db),
    sa: SuperAdmin = Depends(get_current_superadmin),
):
    rows = db.execute(select(Empresa).order_by(Empresa.id.asc())).scalars().all()
    return [{"id": e.id, "nombre": e.nombre, "activo": e.activo, "created_at": str(e.created_at)} for e in rows]