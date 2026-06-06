import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.product import Product
from app.models.stock import Stock
from app.models.etagere import Etagere
from app.models.depot import Depot
from app.models.removal_watch import RemovalWatch
from app.models.alert import Alert

from app.services.removal_watch_service import RemovalWatchService


@pytest.fixture()
def db_session():
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_upsert_and_process_expired_watch(db_session):
    # create product, stock, etagere
    prod = Product(product_code='P001', name='Test Perfume')
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    stock = Stock(product_id=prod.id, product_name=prod.name, quantity_stock=5)
    db_session.add(stock)

    etag = Etagere(etagere_code='E01', depot_id=1, product_id=prod.id, name='Shelf 1', quantity_etagere=1)
    db_session.add(etag)
    db_session.commit()

    service = RemovalWatchService(timeout_minutes=2)

    # report presence with count=2
    watch = service.upsert_presence(db_session, 'E01', prod.id, count=2)
    assert watch.last_count == 2

    # simulate last_seen older than timeout
    old_time = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=3)
    watch.last_seen = old_time
    db_session.commit()

    # process expired watches
    service.process_expired_watches(db_session)

    # stock should be decremented by 2
    updated_stock = db_session.query(Stock).filter(Stock.product_id == prod.id).first()
    assert updated_stock.quantity_stock == 3

    # alert should be created
    alert = db_session.query(Alert).filter(Alert.product_id == prod.id).first()
    assert alert is not None
    assert alert.alert_type == 'missing'

    # watch should be marked processed
    w = db_session.query(RemovalWatch).filter(RemovalWatch.id == watch.id).first()
    assert w.processed is True


def test_presence_endpoint_integration(monkeypatch):
    # create in-memory DB and patch SessionLocal
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    import app.db as app_db
    monkeypatch.setattr(app_db, 'SessionLocal', TestingSessionLocal)

    # Seed DB with product and stock
    db = TestingSessionLocal()
    prod = Product(product_code='P002', name='Integration Perfume')
    db.add(prod)
    db.commit()
    db.refresh(prod)
    stock = Stock(product_id=prod.id, product_name=prod.name, quantity_stock=4)
    db.add(stock)
    etag = Etagere(etagere_code='E02', depot_id=1, product_id=prod.id, name='Shelf 2', quantity_etagere=1)
    db.add(etag)
    db.commit()

    # Call the detection presence handler directly
    from app.routers.detection import report_presence, PresencePayload

    payload = PresencePayload(etagere_code='E02', product_id=prod.id, count=1)
    resp = report_presence(payload, db)
    assert resp.get('message') == 'presence recorded'

    # Expire the watch and process
    watch = db.query(RemovalWatch).filter(RemovalWatch.product_id == prod.id).first()
    assert watch is not None
    watch.last_seen = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=3)
    db.commit()

    svc = RemovalWatchService(timeout_minutes=2)
    svc.process_expired_watches(db)

    updated_stock = db.query(Stock).filter(Stock.product_id == prod.id).first()
    assert updated_stock.quantity_stock == 3

    alert = db.query(Alert).filter(Alert.product_id == prod.id).first()
    assert alert is not None

    db.close()
