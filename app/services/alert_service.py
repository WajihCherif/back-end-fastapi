from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.models.alert import Alert

class AlertService:
    
    def get_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        return db.query(Alert).order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
    
    def get_alert(self, db: Session, alert_id: int) -> Optional[Alert]:
        return db.query(Alert).filter(Alert.id == alert_id).first()
    
    def create_alert(
        self, 
        db: Session, 
        product_id: int, 
        product_name: str,
        alert_type: str,
        expected_quantity: int,
        actual_quantity: int,
        message: str,
        quantity_stock: int = 0,
        quantity_etagere: int = 0,
        quantity_depot: int = 0,
        stock_id: Optional[int] = None,
        etagere_id: Optional[int] = None,
        depot_id: Optional[int] = None
    ) -> Alert:
        alert = Alert(
            product_id=product_id,
            product_name=product_name,
            alert_type=alert_type,
            expected_quantity=expected_quantity,
            actual_quantity=actual_quantity,
            difference=expected_quantity - actual_quantity,
            message=message,
            quantity_stock=quantity_stock,
            quantity_etagere=quantity_etagere,
            quantity_depot=quantity_depot,
            stock_id=stock_id,
            etagere_id=etagere_id,
            depot_id=depot_id
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
