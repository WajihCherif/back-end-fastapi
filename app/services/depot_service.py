from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.depot import Depot
from app.schemas.depot import DepotCreate, DepotUpdate

class DepotService:
    
    def get_depot(self, db: Session, depot_id: int) -> Optional[Depot]:
        return db.query(Depot).filter(Depot.id == depot_id).first()
    
    def get_depot_by_code(self, db: Session, depot_code: str) -> Optional[Depot]:
        return db.query(Depot).filter(Depot.depot_code == depot_code).first()
    
    def get_depots(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[Depot]:
        query = db.query(Depot)
        
        if search:
            query = query.filter(
                or_(
                    Depot.name.contains(search),
                    Depot.depot_code.contains(search),
                    Depot.location.contains(search),
                    Depot.manager_name.contains(search)
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    def create_depot(self, db: Session, depot: DepotCreate) -> Depot:
        existing = self.get_depot_by_code(db, depot.depot_code)
        if existing:
            raise ValueError(f"Depot with code {depot.depot_code} already exists")
        
        db_depot = Depot(**depot.model_dump())
        db.add(db_depot)
        db.commit()
        db.refresh(db_depot)
        return db_depot
    
    def update_depot(
        self, 
        db: Session, 
        depot_id: int, 
        depot_update: DepotUpdate
    ) -> Optional[Depot]:
        db_depot = self.get_depot(db, depot_id)
        if not db_depot:
            return None
        
        update_data = depot_update.model_dump(exclude_unset=True)
        
        if "depot_code" in update_data:
            existing = self.get_depot_by_code(db, update_data["depot_code"])
            if existing and existing.id != depot_id:
                raise ValueError(f"Depot with code {update_data['depot_code']} already exists")
        
        for field, value in update_data.items():
            setattr(db_depot, field, value)
        
        db.commit()
        db.refresh(db_depot)
        return db_depot
    
    def delete_depot(self, db: Session, depot_id: int) -> bool:
        db_depot = self.get_depot(db, depot_id)
        if not db_depot:
            return False
        
        db.delete(db_depot)
        db.commit()
        return True
