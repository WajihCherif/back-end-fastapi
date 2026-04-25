from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.db import Base

class Transfer(Base):
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(200), nullable=False)
    from_location = Column(Enum('stock', 'depot', 'etagere'))
    to_location = Column(Enum('stock', 'depot', 'etagere'))
    quantity = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    transferred_at = Column(DateTime(timezone=True), server_default=func.now())
