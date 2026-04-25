from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas.alert import AlertResponse, AlertCreate
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])
alert_service = AlertService()

@router.get("/", response_model=List[AlertResponse])
def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return alert_service.get_alerts(db, skip=skip, limit=limit)

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = alert_service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/manual", response_model=AlertResponse)
def create_manual_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    alert = alert_service.create_alert(
        db=db,
        product_id=alert_data.product_id,
        product_name=alert_data.product_name,
        alert_type=alert_data.alert_type,
        expected_quantity=alert_data.expected_quantity,
        actual_quantity=alert_data.actual_quantity,
        message=alert_data.message,
        quantity_stock=alert_data.quantity_stock,
        quantity_etagere=alert_data.quantity_etagere,
        quantity_depot=alert_data.quantity_depot
    )
    return alert
