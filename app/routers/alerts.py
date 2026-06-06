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
    from app.models.stock import Stock
    from app.models.etagere import Etagere
    from app.models.depot import Depot

    qty_stock = alert_data.quantity_stock
    qty_etagere = alert_data.quantity_etagere
    qty_depot = alert_data.quantity_depot

    # Query DB records to auto-resolve snapshot quantities and foreign key IDs if not provided
    stock_record = db.query(Stock).filter(Stock.product_id == alert_data.product_id).first()
    etagere_record = db.query(Etagere).filter(Etagere.product_id == alert_data.product_id).first()

    stock_id = stock_record.id if stock_record else None
    etagere_id = etagere_record.id if etagere_record else None
    depot_id = None

    if qty_stock == 0 and stock_record:
        qty_stock = stock_record.quantity_stock

    if qty_etagere == 0 and etagere_record:
        qty_etagere = etagere_record.quantity_etagere

    if etagere_record:
        depot_id = etagere_record.depot_id
        depot_record = db.query(Depot).filter(Depot.id == depot_id).first()
        if qty_depot == 0 and depot_record:
            qty_depot = depot_record.quantity_depot

    alert = alert_service.create_alert(
        db=db,
        product_id=alert_data.product_id,
        product_name=alert_data.product_name,
        alert_type=alert_data.alert_type,
        expected_quantity=alert_data.expected_quantity,
        actual_quantity=alert_data.actual_quantity,
        message=alert_data.message,
        quantity_stock=qty_stock,
        quantity_etagere=qty_etagere,
        quantity_depot=qty_depot,
        stock_id=stock_id,
        etagere_id=etagere_id,
        depot_id=depot_id,
        etagere_code=getattr(alert_data, 'etagere_code', None),
        boxes_missing_count=alert_data.boxes_missing_count,
        state_change_time=alert_data.state_change_time,
        timeout_minutes=alert_data.timeout_minutes
    )
    return alert

@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    success = alert_service.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}
