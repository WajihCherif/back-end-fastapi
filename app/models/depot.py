from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db import Base

class Depot(Base):
    __tablename__ = "depot"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    depot_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200))
    address = Column(Text)
    manager_name = Column(String(100))
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
