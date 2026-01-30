from pydantic import BaseModel

class DashboardSummary(BaseModel):
    ventas_total: float
    tickets: int
    top_productos: list[dict]
    stock_bajo: list[dict]