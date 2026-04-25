from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.stock import Stock
from app.schemas.stock import StockUpdate

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
