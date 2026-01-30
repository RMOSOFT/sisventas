from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.cliente import Cliente

def search_clientes(db: Session, empresa_id: int, q: str, limit: int = 15):
    q = (q or "").strip()
    if not q:
        return []

    like = f"%{q}%"
    stmt = (
        select(Cliente)
        .where(
            Cliente.empresa_id == empresa_id,
            or_(
                Cliente.num_doc.ilike(like),
                Cliente.razon_social.ilike(like),
            ),
        )
        .order_by(Cliente.id.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()

def get_by_num_doc(db: Session, empresa_id: int, num_doc: str):
    stmt = select(Cliente).where(Cliente.empresa_id == empresa_id, Cliente.num_doc == num_doc)
    return db.execute(stmt).scalar_one_or_none()

def create_cliente(db: Session, empresa_id: int, payload: dict):
    # evita duplicados por empresa
    existing = get_by_num_doc(db, empresa_id, payload["num_doc"])
    if existing:
        return existing

    c = Cliente(
        empresa_id=empresa_id,
        tipo_doc=payload["tipo_doc"],
        num_doc=payload["num_doc"],
        razon_social=payload["razon_social"],
        direccion=payload.get("direccion"),
        telefono=payload.get("telefono"),
        email=payload.get("email"),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c