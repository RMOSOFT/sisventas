from pydantic import BaseModel, EmailStr
from typing import Literal

RolUsuario = Literal["admin", "vendedor"]

class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str | None = None
    email: EmailStr
    username: str | None = None
    telefono: str | None = None
    rol: RolUsuario = "vendedor"

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    apellido: str | None
    email: EmailStr
    username: str | None
    telefono: str | None
    rol: str
    activo: bool
    class Config:
        from_attributes = True