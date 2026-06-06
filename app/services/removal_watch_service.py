from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.models.removal_watch import RemovalWatch
from app.models.stock import Stock
from app.models.etagere import Etagere
from app.models.product import Product
from app.services.alert_service import AlertService
import logging

logger = logging.getLogger(__name__)


class RemovalWatchService:
    def __init__(self, timeout_minutes: int = 2):
        self.timeout_minutes = timeout_minutes
        self.alert_service = AlertService()

    def upsert_presence(self, db: Session, etagere_code: str, product_id: int, count: int = 1) -> RemovalWatch:
        # Presence reported -> update or create watch and mark as unprocessed
        watch = (
            db.query(RemovalWatch)
            .filter(RemovalWatch.etagere_code == etagere_code, RemovalWatch.product_id == product_id)
            .first()
        )
        now = datetime.now(datetime.now().astimezone().tzinfo)
        if watch:
            watch.last_seen = now
            watch.last_count = count or 1
            watch.processed = False
        else:
            watch = RemovalWatch(etagere_code=etagere_code, product_id=product_id, last_seen=now, last_count=count or 1, processed=False)
            db.add(watch)

        db.commit()
        db.refresh(watch)
        return watch

    def process_expired_watches(self, db: Session):
        cutoff = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=self.timeout_minutes)
        expired = (
            db.query(RemovalWatch)
            .filter(RemovalWatch.last_seen < cutoff, RemovalWatch.processed == False)
            .all()
        )

        for watch in expired:
            # Load related records
            etagere = db.query(Etagere).filter(Etagere.etagere_code == watch.etagere_code).first()
            stock = db.query(Stock).filter(Stock.product_id == watch.product_id).first()
            product = db.query(Product).filter(Product.id == watch.product_id).first()

            # Decrement stock by 1 (ensure non-negative)
            decrement = getattr(watch, 'last_count', 1) or 1
            if stock and stock.quantity_stock is not None and stock.quantity_stock > 0:
                new_qty = max(0, stock.quantity_stock - decrement)
                logger.info(f"Decrementing stock for product_id={watch.product_id} by {decrement} (from {stock.quantity_stock} to {new_qty})")
                stock.quantity_stock = new_qty
                db.commit()
                db.refresh(stock)

            # Create alert via AlertService
            product_name = product.name if product else (stock.product_name if stock else "Unknown")
            expected_qty = (stock.quantity_stock + decrement) if stock and stock.quantity_stock is not None else decrement
            actual_qty = stock.quantity_stock if stock and stock.quantity_stock is not None else 0

            message = f"Automatic: product {product_name} (id={watch.product_id}) removed from {watch.etagere_code} and not returned within {self.timeout_minutes} minutes."

            try:
                self.alert_service.create_alert(
                db=db,
                product_id=watch.product_id,
                product_name=product_name,
                alert_type="missing",
                expected_quantity=expected_qty,
                actual_quantity=actual_qty,
                message=message,
                quantity_stock=stock.quantity_stock if stock else 0,
                    quantity_etagere=etagere.quantity_etagere if etagere else 0,
                quantity_depot=0,
                stock_id=stock.id if stock else None,
                etagere_id=etagere.id if etagere else None,
                    depot_id=etagere.depot_id if etagere else None,
                    etagere_code=watch.etagere_code,
                boxes_missing_count=0,
                timeout_minutes=self.timeout_minutes
                )
            except Exception as e:
                logger.exception(f"Failed to create alert for watch id={watch.id}: {e}")

            # Mark processed
            watch.processed = True
            db.commit()
