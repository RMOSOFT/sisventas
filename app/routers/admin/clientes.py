from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteOut, ClienteCreate, ClienteMini
from app.crud import cliente as crud
from app.services.lookup import lookup_document, LookupNotConfigured, LookupError

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.get("/search", response_model=list[ClienteMini])
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.search_clientes(db, user.empresa_id, q, limit=15)

@router.post("", response_model=ClienteOut)
def create(payload: ClienteCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.create_cliente(db, user.empresa_id, payload.model_dump())


# Funcion para ver si hay proveedor o no 
@router.get("/lookup")
async def lookup(
    tipo: str = Query(..., description="DNI o RUC"),
    num: str = Query(..., description="Número"),
    user: Usuario = Depends(get_current_user),
):
    tipo = tipo.strip().upper()
    num = num.strip()

    if tipo not in {"DNI", "RUC"}:
        raise HTTPException(400, "tipo inválido (DNI/RUC)")
    if not num.isdigit():
        raise HTTPException(400, "num debe ser numérico")
    if tipo == "DNI" and len(num) != 8:
        raise HTTPException(400, "DNI debe tener 8 dígitos")
    if tipo == "RUC" and len(num) != 11:
        raise HTTPException(400, "RUC debe tener 11 dígitos")

    try:
        data = await lookup_document(tipo, num)
        return {"enabled": True, "data": data}
    except LookupNotConfigured as e:
        return {"enabled": False, "detail": str(e)}
    except LookupError as e:
        return {"enabled": True, "found": False, "detail": str(e)}
        #raise HTTPException(502, str(e))