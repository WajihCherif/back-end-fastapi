from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.transfer import TransferRequest, TransferResponse, TransferHistory
from app.services.transfer_service import TransferService
from app.models.product import Product
from app.models.depot import Depot
from app.models.etagere import Etagere

router = APIRouter(prefix="/transfers", tags=["Transfers"])
transfer_service = TransferService()

@router.post("/depot-to-etagere", response_model=TransferResponse)
def transfer_depot_to_etagere(
    transfer: TransferRequest,
    db: Session = Depends(get_db)
):
    """
    Transfer product from depot to etagere (shelf)
    """
    try:
        result = transfer_service.transfer_product(db, transfer)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/etagere-to-depot", response_model=TransferResponse)
def transfer_etagere_to_depot(
    product_id: int,
    from_etagere_id: int,
    to_depot_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    """
    Transfer product from etagere back to depot
    """
    try:
        result = transfer_service.transfer_from_etagere_to_depot(
            db, product_id, from_etagere_id, to_depot_id, quantity
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-shelves")
def get_available_shelves(
    depot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all shelves with their current stock and capacity
    """
    query = db.query(Etagere)
    
    if depot_id:
        query = query.filter(Etagere.depot_id == depot_id)
    
    shelves = query.all()
    
    result = []
    for shelf in shelves:
        result.append({
            "id": shelf.id,
            "etagere_code": shelf.etagere_code,
            "name": shelf.name,
            "depot_id": shelf.depot_id,
            "current_quantity": shelf.quantity or 0,
            "max_capacity": shelf.max_capacity,
            "available_space": shelf.max_capacity - (shelf.quantity or 0),
            "current_product_id": shelf.product_id
        })
    
    return result

@router.get("/available-products")
def get_available_products(
    depot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all products available for transfer
    """
    products = db.query(Product).all()
    
    result = []
    for product in products:
        # Get current stock on shelves
        shelf_stock = db.query(Etagere).filter(
            Etagere.product_id == product.id
        ).all()
        
        total_on_shelves = sum(s.quantity or 0 for s in shelf_stock)
        
        result.append({
            "id": product.id,
            "name": product.name,
            "product_code": product.product_code,
            "barcode": product.barcode,
            "price": product.price,
            "total_on_shelves": total_on_shelves
        })
    
    return result

@router.get("/depot-stock/{depot_id}")
def get_depot_stock(
    depot_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all products in a depot (simplified)
    """
    # Get all shelves in this depot
    shelves = db.query(Etagere).filter(Etagere.depot_id == depot_id).all()
    
    # Group by product
    stock_by_product = {}
    for shelf in shelves:
        if shelf.product_id:
            if shelf.product_id not in stock_by_product:
                product = db.query(Product).filter(Product.id == shelf.product_id).first()
                stock_by_product[shelf.product_id] = {
                    "product_id": shelf.product_id,
                    "product_name": product.name if product else "Unknown",
                    "product_code": product.product_code if product else "Unknown",
                    "quantity": 0,
                    "shelves": []
                }
            stock_by_product[shelf.product_id]["quantity"] += shelf.quantity or 0
            stock_by_product[shelf.product_id]["shelves"].append({
                "shelf_id": shelf.id,
                "shelf_name": shelf.name,
                "quantity": shelf.quantity or 0
            })
    
    return list(stock_by_product.values())
