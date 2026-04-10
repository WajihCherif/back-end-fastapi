from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class Etagere(Base):
    __tablename__ = "etagere"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    etagere_code = Column(String(50), unique=True, nullable=False, index=True)
    depot_id = Column(Integer, ForeignKey("depot.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    name = Column(String(100), nullable=False)
    section = Column(String(50))
    quantity = Column(Integer, default=0)
    max_capacity = Column(Integer, default=100)
    last_restocked = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    depot = relationship("Depot", foreign_keys=[depot_id])
    product = relationship("Product", foreign_keys=[product_id])
