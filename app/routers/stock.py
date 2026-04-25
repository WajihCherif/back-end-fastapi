from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.stock import StockResponse, StockUpdate
from app.services.stock_service import StockService

router = APIRouter(prefix="/stock", tags=["Stock"])
stock_service = StockService()

@router.get("/", response_model=List[StockResponse])
def get_all_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return stock_service.get_all_stock(db, skip=skip, limit=limit)

@router.get("/{product_id}", response_model=StockResponse)
def get_stock_by_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    stock = stock_service.get_stock_by_product(db, product_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock entry not found for this product")
    return stock

@router.get("/by-barcode/{barcode}", response_model=StockResponse)
def get_stock_by_barcode(
    barcode: str,
    db: Session = Depends(get_db)
):
    stock = stock_service.get_stock_by_barcode(db, barcode)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock entry not found for this barcode")
    return stock

@router.put("/{product_id}", response_model=StockResponse)
def update_stock(
    product_id: int,
    stock_update: StockUpdate,
    db: Session = Depends(get_db)
):
    stock = stock_service.update_stock_quantity(db, product_id, stock_update.quantity_stock)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock entry not found")
    return stock
