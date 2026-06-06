from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from app.models.alert import Alert

class AlertService:
    
    def get_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alert]:
        alerts = db.query(Alert).order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
        
        # Attach live quantities from relationships
        for alert in alerts:
            alert.live_stock_qty = alert.stock.quantity_stock if alert.stock else None
            alert.live_etagere_qty = alert.etagere.quantity_etagere if alert.etagere else None
            alert.live_depot_qty = alert.depot.quantity_depot if alert.depot else None
            
        return alerts
    
    def get_alert(self, db: Session, alert_id: int) -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.live_stock_qty = alert.stock.quantity_stock if alert.stock else None
            alert.live_etagere_qty = alert.etagere.quantity_etagere if alert.etagere else None
            alert.live_depot_qty = alert.depot.quantity_depot if alert.depot else None
        return alert
    
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
        depot_id: Optional[int] = None,
        boxes_missing_count: int = 0,
        state_change_time: Optional[datetime] = None,
        timeout_minutes: int = 5,
        etagere_code: Optional[str] = None
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
            depot_id=depot_id,
            etagere_code=etagere_code,
            boxes_missing_count=boxes_missing_count,
            state_change_time=state_change_time or datetime.now(datetime.now().astimezone().tzinfo),
            timeout_minutes=timeout_minutes
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def delete_alert(self, db: Session, alert_id: int) -> bool:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            db.delete(alert)
            db.commit()
            return True
        return False
