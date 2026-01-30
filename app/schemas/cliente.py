from pydantic import BaseModel, Field

class ClienteOut(BaseModel):
    id: int
    tipo_doc: str
    num_doc: str
    razon_social: str
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True

class ClienteCreate(BaseModel):
    tipo_doc: str = Field(..., examples=["DNI", "RUC", "CE"])
    num_doc: str
    razon_social: str
    direccion: str | None = None
    telefono: str | None = None
    email: str | None = None

class ClienteMini(BaseModel):
    id: int
    tipo_doc: str
    num_doc: str
    razon_social: str
    direccion: str | None = None

    class Config:
        from_attributes = True