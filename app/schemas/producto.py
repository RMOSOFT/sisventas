from pydantic import BaseModel, Field

class ProductoCreate(BaseModel):
    nombre: str
    categoria_id: int | None = None
    sku: str | None = None
    precio: float = Field(ge=0)
    costo: float = Field(ge=0)
    stock_actual: float = Field(ge=0, default=0)
    stock_minimo: float = Field(ge=0, default=0)
    activo: bool = True

class ProductoOut(BaseModel):
    id: int
    nombre: str
    sku: str | None
    precio: float
    costo: float
    stock_actual: float
    stock_minimo: float
    activo: bool
    class Config:
        from_attributes = True