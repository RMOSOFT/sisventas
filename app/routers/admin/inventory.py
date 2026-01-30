from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.schemas.inventario import MovimientoCreate
from app.crud import inventario as crud
from app.auth.deps import get_current_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/inventory", tags=["inventory"])

# EMPRESA_ID = 1
# USER_ID = 1


# Funcion mejorada para crear movimientos
@router.post("/movements")
def create_movement(payload: MovimientoCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return crud.create_movement(db, user.empresa_id, user.id, payload.model_dump())
"""
@router.post("/movements")
def create_movement(payload: MovimientoCreate, db: Session = Depends(get_db)):
    return crud.create_movement(db, EMPRESA_ID, USER_ID, payload.model_dump())
"""

# Funcion mejorada para ver los stock
@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    items = crud.low_stock(db, user.empresa_id)
    return [{"id": p.id, "nombre": p.nombre, "stock": float(p.stock_actual), "min": float(p.stock_minimo)} for p in items]
"""
@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db)):
    items = crud.low_stock(db, EMPRESA_ID)
    return [{"id": p.id, "nombre": p.nombre, "stock": float(p.stock_actual), "min": float(p.stock_minimo)} for p in items]
"""



