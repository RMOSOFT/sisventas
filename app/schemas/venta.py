from pydantic import BaseModel, Field
from datetime import datetime

# Backend para listar productos
class VentaItemIn(BaseModel):
    producto_id: int
    cantidad: float = Field(gt=0)
    descuento: float = Field(ge=0, default=0)

# Backend para crear productos
class VentaCreate(BaseModel):
    items: list[VentaItemIn]
    descuento_total: float = Field(ge=0, default=0)
    metodo_pago: str = "efectivo"

    cliente_id: int | None = None
    #efectivo_recibido: float | None = 0
    efectivo_recibido: float = Field(default=0, ge=0)


class VentaOut(BaseModel):
    id: int
    numero: int
    total: float
    estado: str
    can_cancel: bool = True
    metodo_pago: str
    efectivo_recibido: float = 0
    vuelto: float = 0
    class Config:
        from_attributes = True

class VentaListOut(BaseModel):
    id: int
    numero: int
    fecha: datetime
    total: float
    metodo_pago: str
    estado: str
    class Config:
        from_attributes = True


class VentaDetalleItemOut(BaseModel):
    producto_id: int
    nombre: str
    cantidad: float
    precio_unitario: float
    descuento: float
    total_linea: float

# Backend para detalles de salida del producto
class VentaDetailOut(BaseModel):
    id: int
    numero: int
    fecha: datetime
    subtotal: float
    descuento_total: float
    total: float
    metodo_pago: str
    estado: str
    items: list[VentaDetalleItemOut]

    efectivo_recibido: float = 0
    vuelto: float = 0
    can_cancel: bool = True

# Backend para anular venta
class VentaCancelIn(BaseModel):
    motivo: str | None = None