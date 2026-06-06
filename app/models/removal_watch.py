from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db import Base


class RemovalWatch(Base):
    __tablename__ = "removal_watch"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    etagere_code = Column(String(50), nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_count = Column(Integer, default=1)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
