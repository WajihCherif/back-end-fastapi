from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertBase(BaseModel):
    product_id: int
    product_name: str
    alert_type: str  # 'missing', 'box_missing', etc.
    expected_quantity: int = 0
    actual_quantity: int = 0
    difference: int = 0
    message: Optional[str] = None
    quantity_stock: int = 0
    quantity_etagere: int = 0
    quantity_depot: int = 0
    etagere_code: Optional[str] = None
    boxes_missing_count: int = 0  # For box_missing alerts
    state_change_time: Optional[datetime] = None  # When count changed
    timeout_minutes: int = 5  # Default timeout

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    etagere_code: Optional[str] = None
    stock_id: Optional[int] = None
    etagere_id: Optional[int] = None
    depot_id: Optional[int] = None
    created_at: datetime
    live_stock_qty: Optional[int] = None
    live_etagere_qty: Optional[int] = None
    live_depot_qty: Optional[int] = None

    class Config:
        from_attributes = True
