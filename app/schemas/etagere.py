from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class EtagereBase(BaseModel):
    etagere_code: str = Field(..., min_length=1, max_length=50)
    depot_id: int
    product_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    section: Optional[str] = None
    quantity_etagere: int = 0
    max_capacity: int = 100

class EtagereCreate(EtagereBase):
    pass

class EtagereUpdate(BaseModel):
    etagere_code: Optional[str] = None
    depot_id: Optional[int] = None
    product_id: Optional[int] = None
    name: Optional[str] = None
    section: Optional[str] = None
    quantity_etagere: Optional[int] = None
    max_capacity: Optional[int] = None

class EtagereResponse(EtagereBase):
    id: int
    last_restocked: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Extended response with depot and product info
class EtagereDetailResponse(EtagereResponse):
    depot_name: Optional[str] = None
    depot_code: Optional[str] = None
    product_name: Optional[str] = None
    product_code: Optional[str] = None
