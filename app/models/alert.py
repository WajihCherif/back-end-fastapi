# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import func
from app.db import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    alert_type = Column(String(100), nullable=False)  # 'missing' | 'box_missing' | other
    expected_quantity = Column(Integer, default=0)
    actual_quantity = Column(Integer, default=0)
    difference = Column(Integer, default=0)
    message = Column(Text)
    
    # Snapshot quantities at the time of alert
    quantity_stock = Column(Integer, default=0)
    quantity_etagere = Column(Integer, default=0)
    quantity_depot = Column(Integer, default=0)
    
    # Box removal tracking fields
    boxes_missing_count = Column(Integer, default=0)  # How many boxes are missing (for box_missing alerts)
    state_change_time = Column(DateTime(timezone=True), nullable=True)  # When detection count changed
    timeout_minutes = Column(Integer, default=5)  # How long before alert fires
    
    # Foreign Keys to the source tables
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=True)
    etagere_id = Column(Integer, ForeignKey("etagere.id"), nullable=True)
    depot_id = Column(Integer, ForeignKey("depot.id"), nullable=True)
    # Human-friendly shelf code snapshot
    etagere_code = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", foreign_keys=[product_id])
    stock = relationship("Stock", foreign_keys=[stock_id])
    etagere = relationship("Etagere", foreign_keys=[etagere_id])
    depot = relationship("Depot", foreign_keys=[depot_id])
