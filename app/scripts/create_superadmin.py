from passlib.context import CryptContext
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.super_admin import SuperAdmin  # ajusta si tu archivo se llama distinto
from sqlalchemy import select, or_, func


pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL = "enmanuelluquerodriguez5@gmail.com"
PASS = "SuperAdmin123!"
NOMBRE = "Enmanuel"
USERNAME = "rmosoft"  # <- obligatorio y en minúsculas

db = SessionLocal()
try:
    email = EMAIL.strip().lower()
    username = USERNAME.strip().lower()

    # si existe por email o username, bórralo (o actualízalo)
    sa = db.execute(
        select(SuperAdmin).where(
            or_(
                func.lower(SuperAdmin.email) == email,
                func.lower(SuperAdmin.username) == username,
            )
        )
    ).scalar_one_or_none()

    #sa = db.execute(
    #    select(SuperAdmin).where(
    #        (SuperAdmin.email == email) | (SuperAdmin.username == username)
    #    )
    #).scalar_one_or_none()

    if sa:
        db.delete(sa)
        db.commit()

    sa = SuperAdmin(
        nombre=NOMBRE,
        apellido=None,
        username=username,        # <- AQUÍ estaba el problema
        email=email,
        password_hash=pwd.hash(PASS),
        activo=True
    )
    db.add(sa)
    db.commit()

    print("✅ SuperAdmin creado")
    print("   username:", username)
    print("   email:", email)
    print("   password:", PASS)

finally:
    db.close()