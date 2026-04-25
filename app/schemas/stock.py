from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StockBase(BaseModel):
    product_id: int
    product_name: str
    barcode: Optional[str] = None
    quantity_stock: int = 0

class StockUpdate(BaseModel):
    quantity_stock: int

class StockResponse(StockBase):
    id: int
    last_update: datetime

    class Config:
        from_attributes = True
