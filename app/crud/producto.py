from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Producto

def list_products(db: Session, empresa_id: int, search: str | None = None):
    stmt = select(Producto).where(Producto.empresa_id == empresa_id, Producto.activo == True)
    if search:
        stmt = stmt.where(Producto.nombre.ilike(f"%{search}%"))
    return db.execute(stmt.order_by(Producto.nombre)).scalars().all()

def get_product(db: Session, empresa_id: int, product_id: int):
    return db.get(Producto, product_id)

def create_product(db: Session, empresa_id: int, data):
    data = dict(data)
    data["unidad"] = (data.get("unidad") or "UND").strip()
    data["marca"] = (data.get("marca") or None)
    
    p = Producto(empresa_id=empresa_id, **data)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p