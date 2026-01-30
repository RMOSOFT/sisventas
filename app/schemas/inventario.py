from pydantic import BaseModel, Field

class MovimientoCreate(BaseModel):
    producto_id: int
    tipo: str  # entrada|salida|ajuste
    cantidad: float = Field(gt=0)
    costo_unitario: float | None = Field(default=None, ge=0)
    referencia: str | None = None