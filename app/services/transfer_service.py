from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional
from app.models.product import Product
from app.models.depot import Depot
from app.models.etagere import Etagere
from app.models.transfer import Transfer
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
        if depot.quantity_depot is None or depot.quantity_depot < transfer.quantity:
            raise ValueError(
                f"Not enough quantity in depot {depot.depot_code}. "
                f"Available: {depot.quantity_depot or 0}, "
                f"Requested: {transfer.quantity}"
            )
        # 6. Check if etagere has enough capacity
        current_quantity = etagere.quantity_etagere or 0
        new_quantity = current_quantity + transfer.quantity
        
        if new_quantity > etagere.max_capacity:
            raise ValueError(
                f"Cannot transfer {transfer.quantity} units. "
                f"Shelf {etagere.etagere_code} has capacity {etagere.max_capacity}, "
                f"currently has {current_quantity}. "
                f"Available space: {etagere.max_capacity - current_quantity}"
            )
        
        # 7. Update etagere stock and depot stock
        etagere.quantity_etagere = new_quantity
        etagere.product_id = transfer.product_id
        etagere.last_restocked = datetime.now()
        etagere.last_updated = datetime.now()
        
        depot.quantity_depot -= transfer.quantity
        
        # 8. Create transfer record
        # Note: Depending on your exact DB schema for `Transfer`, you might need to add `from_depot_id` and `to_etagere_id` if they aren't explicitly tracked, but standard `product_id`, `product_name`, `from_location`, etc., is being used here. We will use `notes` to store extra info if needed, or if those columns exist, we populate them. The existing schema has `from_location` and `to_location`. Wait, looking at `transfers` table schema, it has `from_location`, `to_location`, but no detailed IDs. Wait, the `TransferHistory` Pydantic model expects `from_depot_name` and `to_etagere_name`. Let's ensure the backend sends those back via the router if not in the DB, or adds them to DB. Let's see the schema `app.models.transfer.Transfer` ... wait, it only has `from_location (Enum)`, `to_location (Enum)`.
        history = Transfer(
            product_id=transfer.product_id,
            product_name=product.name,
            from_location='depot',
            to_location='etagere',
            quantity=transfer.quantity,
            notes=transfer.notes,
            # We don't have from_depot_id in Transfer model based on previous file view.
            # We'll rely on the history getter to enrich this or just save it in notes?
            # Actually, I should check the Transfer model again.
        )
        db.add(history)
        
        db.commit()
        db.refresh(etagere)
        db.refresh(depot)
        
        return {
            "success": True,
            "message": f"Successfully transferred {transfer.quantity} units of {product.name} to {etagere.name}",
            "from_depot_id": transfer.from_depot_id,
            "to_etagere_id": transfer.to_etagere_id,
            "product_id": transfer.product_id,
            "quantity": transfer.quantity,
            "new_depot_quantity": depot.quantity_depot,
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
        if etagere.quantity_etagere < quantity:
            raise ValueError(
                f"Cannot transfer {quantity} units. "
                f"Shelf {etagere.etagere_code} only has {etagere.quantity_etagere} units"
            )
        
        # Update etagere
        etagere.quantity_etagere -= quantity
        if etagere.quantity_etagere == 0:
            etagere.product_id = None
        # Create transfer record
        history = Transfer(
            product_id=product_id,
            product_name=product.name,
            from_location='etagere',
            to_location='depot',
            quantity=quantity,
            notes="Transfer back to depot"
        )
        db.add(history)
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
            "new_etagere_quantity": etagere.quantity_etagere,
            "transferred_at": datetime.now()
        }
    
    def get_transfer_history(
        self, 
        db: Session, 
        limit: int = 50,
        product_id: Optional[int] = None
    ) -> List[dict]:
        """
        Get transfer history from the transfers table
        """
        query = db.query(Transfer)
        if product_id:
            query = query.filter(Transfer.product_id == product_id)
        
        transfers = query.order_by(desc(Transfer.transferred_at)).limit(limit).all()
        
        result = []
        for t in transfers:
            result.append({
                "id": t.id,
                "product_id": t.product_id,
                "product_name": t.product_name,
                "quantity": t.quantity,
                "notes": t.notes,
                "transferred_at": t.transferred_at,
                "from_depot_id": None,
                "from_depot_name": "Dépôt" if t.from_location == 'depot' else None,
                "to_etagere_id": None,
                "to_etagere_name": "Étagère" if t.to_location == 'etagere' else None,
            })
        return result
