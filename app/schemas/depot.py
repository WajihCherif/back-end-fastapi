from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DepotBase(BaseModel):
    depot_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = None
    address: Optional[str] = None
    manager_name: Optional[str] = None
    phone: Optional[str] = None

class DepotCreate(DepotBase):
    pass

class DepotUpdate(BaseModel):
    depot_code: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    manager_name: Optional[str] = None
    phone: Optional[str] = None

class DepotResponse(DepotBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
