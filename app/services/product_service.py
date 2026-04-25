from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.product import Product
from app.models.stock import Stock
from app.schemas.product import ProductCreate, ProductUpdate

class ProductService:
    
    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()
    
    def get_product_by_code(self, db: Session, product_code: str) -> Optional[Product]:
        return db.query(Product).filter(Product.product_code == product_code).first()
    
    def get_product_by_barcode(self, db: Session, barcode: str) -> Optional[Product]:
        stock_entry = db.query(Stock).filter(Stock.barcode == barcode).first()
        if stock_entry:
            return self.get_product(db, stock_entry.product_id)
        return None
    
    def get_products(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Product]:
        query = db.query(Product)
        
        if search:
            query = query.filter(
                or_(
                    Product.name.contains(search),
                    Product.product_code.contains(search),
                    Product.category.contains(search)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def create_product(self, db: Session, product: ProductCreate) -> Product:
        existing = self.get_product_by_code(db, product.product_code)
        if existing:
            raise ValueError(f"Product with code {product.product_code} already exists")
        
        
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    def update_product(
        self, 
        db: Session, 
        product_id: int, 
        product_update: ProductUpdate
    ) -> Optional[Product]:
        db_product = self.get_product(db, product_id)
        if not db_product:
            return None
        
        update_data = product_update.model_dump(exclude_unset=True)
        
        if "product_code" in update_data:
            existing = self.get_product_by_code(db, update_data["product_code"])
            if existing and existing.id != product_id:
                raise ValueError(f"Product with code {update_data['product_code']} already exists")
        
        
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db.commit()
        db.refresh(db_product)
        return db_product
    
    def delete_product(self, db: Session, product_id: int) -> bool:
        db_product = self.get_product(db, product_id)
        if not db_product:
            return False
        
        db.delete(db_product)
        db.commit()
        return True
