from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    product_id: int
    product_name: str
    alert_type: str
    expected_quantity: int = 0
    actual_quantity: int = 0
    difference: int = 0
    message: Optional[str] = None
    quantity_stock: int = 0
    quantity_etagere: int = 0
    quantity_depot: int = 0

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    stock_id: Optional[int] = None
    etagere_id: Optional[int] = None
    depot_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
