from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime
from app.models.etagere import Etagere
from app.models.depot import Depot
from app.models.product import Product
from app.schemas.etagere import EtagereCreate, EtagereUpdate

class EtagereService:
    
    def get_etagere(self, db: Session, etagere_id: int) -> Optional[Etagere]:
        return db.query(Etagere).filter(Etagere.id == etagere_id).first()
    
    def get_etagere_by_code(self, db: Session, etagere_code: str) -> Optional[Etagere]:
        return db.query(Etagere).filter(Etagere.etagere_code == etagere_code).first()
    
    def get_etageres(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        depot_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Etagere]:
        query = db.query(Etagere)
        
        if depot_id:
            query = query.filter(Etagere.depot_id == depot_id)
        
        if search:
            query = query.filter(
                or_(
                    Etagere.name.contains(search),
                    Etagere.etagere_code.contains(search),
                    Etagere.section.contains(search)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_etagere_details(self, db: Session, etagere_id: int) -> Optional[dict]:
        etagere = self.get_etagere(db, etagere_id)
        if not etagere:
            return None
        
        depot = db.query(Depot).filter(Depot.id == etagere.depot_id).first()
        product = db.query(Product).filter(Product.id == etagere.product_id).first() if etagere.product_id else None
        
        return {
            "id": etagere.id,
            "etagere_code": etagere.etagere_code,
            "depot_id": etagere.depot_id,
            "depot_name": depot.name if depot else None,
            "depot_code": depot.depot_code if depot else None,
            "product_id": etagere.product_id,
            "product_name": product.name if product else None,
            "product_code": product.product_code if product else None,
            "name": etagere.name,
            "section": etagere.section,
            "quantity": etagere.quantity,
            "max_capacity": etagere.max_capacity,
            "last_restocked": etagere.last_restocked,
            "last_updated": etagere.last_updated
        }
    
    def get_etagere_details_by_code(self, db: Session, etagere_code: str) -> Optional[dict]:
        etagere = self.get_etagere_by_code(db, etagere_code)
        if not etagere:
            return None
        return self.get_etagere_details(db, etagere.id)
    
    def create_etagere(self, db: Session, etagere: EtagereCreate) -> Etagere:
        existing = self.get_etagere_by_code(db, etagere.etagere_code)
        if existing:
            raise ValueError(f"Etagere with code {etagere.etagere_code} already exists")
        
        depot = db.query(Depot).filter(Depot.id == etagere.depot_id).first()
        if not depot:
            raise ValueError(f"Depot with id {etagere.depot_id} not found")
        
        if etagere.product_id:
            product = db.query(Product).filter(Product.id == etagere.product_id).first()
            if not product:
                raise ValueError(f"Product with id {etagere.product_id} not found")
        
        db_etagere = Etagere(**etagere.model_dump())
        db.add(db_etagere)
        db.commit()
        db.refresh(db_etagere)
        return db_etagere
    
    def update_etagere(
        self, 
        db: Session, 
        etagere_id: int, 
        etagere_update: EtagereUpdate
    ) -> Optional[Etagere]:
        db_etagere = self.get_etagere(db, etagere_id)
        if not db_etagere:
            return None
        
        update_data = etagere_update.model_dump(exclude_unset=True)
        
        if "etagere_code" in update_data:
            existing = self.get_etagere_by_code(db, update_data["etagere_code"])
            if existing and existing.id != etagere_id:
                raise ValueError(f"Etagere with code {update_data['etagere_code']} already exists")
        
        if "depot_id" in update_data:
            depot = db.query(Depot).filter(Depot.id == update_data["depot_id"]).first()
            if not depot:
                raise ValueError(f"Depot with id {update_data['depot_id']} not found")
        
        if "product_id" in update_data and update_data["product_id"]:
            product = db.query(Product).filter(Product.id == update_data["product_id"]).first()
            if not product:
                raise ValueError(f"Product with id {update_data['product_id']} not found")
        
        for field, value in update_data.items():
            setattr(db_etagere, field, value)
        
        db.commit()
        db.refresh(db_etagere)
        return db_etagere
    
    def update_stock(self, db: Session, etagere_code: str, new_quantity: int) -> Optional[Etagere]:
        etagere = self.get_etagere_by_code(db, etagere_code)
        if not etagere:
            return None
        
        etagere.quantity = new_quantity
        etagere.last_updated = datetime.now()
        
        db.commit()
        db.refresh(etagere)
        return etagere
    
    def restock_etagere(self, db: Session, etagere_code: str) -> Optional[Etagere]:
        etagere = self.get_etagere_by_code(db, etagere_code)
        if not etagere:
            return None
        
        etagere.quantity = etagere.max_capacity
        etagere.last_restocked = datetime.now()
        etagere.last_updated = datetime.now()
        
        db.commit()
        db.refresh(etagere)
        return etagere
    
    def delete_etagere(self, db: Session, etagere_id: int) -> bool:
        db_etagere = self.get_etagere(db, etagere_id)
        if not db_etagere:
            return False
        
        db.delete(db_etagere)
        db.commit()
        return True
