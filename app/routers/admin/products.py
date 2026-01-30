from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.auth.deps import get_current_user
from app.schemas.producto import ProductoCreate, ProductoOut
from app.crud import producto as crud
from app.models import Usuario, Empresa

router = APIRouter(prefix="/products", tags=["products"])

# MVP: empresa fija 1 (luego auth real multi-empresa)
# EMPRESA_ID = 1


# Funcion mejorada para listar productos
@router.get("", response_model=list[ProductoOut])
def list_products(search: str | None = Query(default=None), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.list_products(db, user.empresa_id, search)
"""
@router.get("", response_model=list[ProductoOut])
def list_products(search: str | None = Query(default=None), db: Session = Depends(get_db)):
    return crud.list_products(db, EMPRESA_ID, search)
"""

# Funcion mejorada para crear productos
@router.post("", response_model=ProductoOut)
def create_product(payload: ProductoCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.create_product(db, user.empresa_id, payload.model_dump())
"""
@router.post("", response_model=ProductoOut)
def create_product(payload: ProductoCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, EMPRESA_ID, payload.model_dump())
"""




