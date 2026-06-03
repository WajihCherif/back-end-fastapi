from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.stock import Stock
from app.models.depot import Depot
from app.models.product import Product
from app.schemas.stock import StockUpdate, AddStockRequest

class StockService:
    
    def get_all_stock(self, db: Session, skip: int = 0, limit: int = 100) -> List[Stock]:
        return db.query(Stock).offset(skip).limit(limit).all()
    
    def get_stock_by_product(self, db: Session, product_id: int) -> Optional[Stock]:
        return db.query(Stock).filter(Stock.product_id == product_id).first()
    
    def get_stock_by_barcode(self, db: Session, barcode: str) -> Optional[Stock]:
        return db.query(Stock).filter(Stock.barcode == barcode).first()
    
    def update_stock_quantity(self, db: Session, product_id: int, quantity: int) -> Optional[Stock]:
        stock = self.get_stock_by_product(db, product_id)
        if not stock:
            return None
        
        stock.quantity_stock = quantity
        db.commit()
        db.refresh(stock)
        return stock

    def create_or_update_stock(self, db: Session, product_id: int, product_name: str, barcode: str, quantity: int) -> Stock:
        stock = self.get_stock_by_product(db, product_id)
        if stock:
            stock.quantity_stock = quantity
            stock.barcode = barcode
            stock.product_name = product_name
        else:
            stock = Stock(
                product_id=product_id,
                product_name=product_name,
                barcode=barcode,
                quantity_stock=quantity
            )
            db.add(stock)
        
        db.commit()
        db.refresh(stock)
        return stock

    def add_stock(self, db: Session, request: AddStockRequest) -> dict:
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise ValueError("Product not found")
            
        depot = db.query(Depot).filter(Depot.id == request.depot_id).first()
        if not depot:
            raise ValueError("Depot not found")
            
        # Update depot stock
        if depot.quantity_depot is None:
            depot.quantity_depot = 0
        depot.quantity_depot += request.quantity
        
        # Update or create global product stock
        stock = self.get_stock_by_product(db, request.product_id)
        if stock:
            stock.quantity_stock += request.quantity
        else:
            stock = Stock(
                product_id=request.product_id,
                product_name=product.name,
                barcode=product.product_code, # Use code as default barcode if not set
                quantity_stock=request.quantity
            )
            db.add(stock)
            
        db.commit()
        db.refresh(depot)
        db.refresh(stock)
        
        return {
            "success": True,
            "message": f"Successfully added {request.quantity} units to {depot.name} for product {product.name}",
            "new_depot_quantity": depot.quantity_depot,
            "new_stock_quantity": stock.quantity_stock
        }
