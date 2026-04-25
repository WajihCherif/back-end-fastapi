from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db import Base

class Stock(Base):
    __tablename__ = "stock"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    barcode = Column(String(100))
    last_update = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    quantity_stock = Column(Integer, default=0)
