from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional
from app.models.product import Product
from app.models.depot import Depot
from app.models.etagere import Etagere
from app.schemas.transfer import TransferRequest, TransferHistory

class TransferService:
    
    def transfer_product(
        self, 
        db: Session, 
        transfer: TransferRequest
    ) -> dict:
        """
        Transfer product from depot to etagere (shelf)
        """
        # 1. Verify product exists
        product = db.query(Product).filter(Product.id == transfer.product_id).first()
        if not product:
            raise ValueError(f"Product with id {transfer.product_id} not found")
        
        # 2. Verify depot exists
        depot = db.query(Depot).filter(Depot.id == transfer.from_depot_id).first()
        if not depot:
            raise ValueError(f"Depot with id {transfer.from_depot_id} not found")
        
        # 3. Verify etagere exists
        etagere = db.query(Etagere).filter(Etagere.id == transfer.to_etagere_id).first()
        if not etagere:
            raise ValueError(f"Etagere with id {transfer.to_etagere_id} not found")
        
        # 4. Check if etagere belongs to the same depot
        if etagere.depot_id != transfer.from_depot_id:
            raise ValueError(f"Etagere {etagere.etagere_code} does not belong to depot {depot.depot_code}")
        
        # 5. Check if we have enough quantity in depot
        # For now, we'll assume depot has unlimited stock
        # You can add depot_stock table to track depot inventory
        
        # 6. Check if etagere has enough capacity
        current_quantity = etagere.quantity or 0
        new_quantity = current_quantity + transfer.quantity
        
        if new_quantity > etagere.max_capacity:
            raise ValueError(
                f"Cannot transfer {transfer.quantity} units. "
                f"Shelf {etagere.etagere_code} has capacity {etagere.max_capacity}, "
                f"currently has {current_quantity}. "
                f"Available space: {etagere.max_capacity - current_quantity}"
            )
        
        # 7. Update etagere stock
        etagere.quantity = new_quantity
        etagere.product_id = transfer.product_id
        etagere.last_restocked = datetime.now()
        etagere.last_updated = datetime.now()
        
        # 8. Create transfer record (optional - you can create a transfers table)
        # For now, we'll just return the result
        
        db.commit()
        db.refresh(etagere)
        
        return {
            "success": True,
            "message": f"Successfully transferred {transfer.quantity} units of {product.name} to {etagere.name}",
            "from_depot_id": transfer.from_depot_id,
            "to_etagere_id": transfer.to_etagere_id,
            "product_id": transfer.product_id,
            "quantity": transfer.quantity,
            "new_depot_quantity": 0,  # You can calculate from depot_stock table
            "new_etagere_quantity": new_quantity,
            "transferred_at": datetime.now()
        }
    
    def transfer_from_etagere_to_depot(
        self,
        db: Session,
        product_id: int,
        from_etagere_id: int,
        to_depot_id: int,
        quantity: int
    ) -> dict:
        """
        Transfer product from etagere back to depot
        """
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        
        # Verify etagere exists
        etagere = db.query(Etagere).filter(Etagere.id == from_etagere_id).first()
        if not etagere:
            raise ValueError(f"Etagere with id {from_etagere_id} not found")
        
        # Verify depot exists
        depot = db.query(Depot).filter(Depot.id == to_depot_id).first()
        if not depot:
            raise ValueError(f"Depot with id {to_depot_id} not found")
        
        # Check if etagere has enough quantity
        if etagere.quantity < quantity:
            raise ValueError(
                f"Cannot transfer {quantity} units. "
                f"Shelf {etagere.etagere_code} only has {etagere.quantity} units"
            )
        
        # Update etagere
        etagere.quantity -= quantity
        if etagere.quantity == 0:
            etagere.product_id = None
        etagere.last_updated = datetime.now()
        
        db.commit()
        db.refresh(etagere)
        
        return {
            "success": True,
            "message": f"Successfully transferred {quantity} units of {product.name} from {etagere.name} to {depot.name}",
            "from_depot_id": to_depot_id,  # This represents the destination depot
            "to_etagere_id": from_etagere_id,  # This represents the source etagere
            "product_id": product_id,
            "quantity": quantity,
            "new_depot_quantity": 0,  # Placeholder for depot stock
            "new_etagere_quantity": etagere.quantity,
            "transferred_at": datetime.now()
        }
    
    def get_transfer_history(
        self, 
        db: Session, 
        limit: int = 50,
        product_id: Optional[int] = None
    ) -> List[dict]:
        """
        Get transfer history (simplified - you would need a transfers table)
        """
        # This is a placeholder. For real implementation, create a transfers table
        return []
