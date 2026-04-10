from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransferRequest(BaseModel):
    product_id: int
    from_depot_id: int
    to_etagere_id: int
    quantity: int
    notes: Optional[str] = None

class TransferResponse(BaseModel):
    success: bool
    message: str
    from_depot_id: int
    to_etagere_id: int
    product_id: int
    quantity: int
    new_depot_quantity: int
    new_etagere_quantity: int
    transferred_at: datetime

class TransferHistory(BaseModel):
    id: int
    product_id: int
    product_name: str
    from_depot_id: int
    from_depot_name: str
    to_etagere_id: int
    to_etagere_name: str
    quantity: int
    notes: Optional[str]
    transferred_at: datetime
