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


def test_no_negative_stock_and_alert_created(db_session):
    # create product with zero stock
    prod = Product(product_code='P100', name='Zero Stock Perfume')
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    stock = Stock(product_id=prod.id, product_name=prod.name, quantity_stock=0)
    db_session.add(stock)
    etag = Etagere(etagere_code='E10', depot_id=1, product_id=prod.id, name='ShelfZ', quantity_etagere=0)
    db_session.add(etag)
    db_session.commit()

    svc = RemovalWatchService(timeout_minutes=2)
    watch = svc.upsert_presence(db_session, 'E10', prod.id, count=2)

    # expire
    watch.last_seen = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=5)
    db_session.commit()

    svc.process_expired_watches(db_session)

    # stock remains 0, not negative
    s = db_session.query(Stock).filter(Stock.product_id == prod.id).first()
    assert s.quantity_stock == 0

    # alert still created
    a = db_session.query(Alert).filter(Alert.product_id == prod.id).first()
    assert a is not None


def test_presence_update_prevents_processing(db_session):
    prod = Product(product_code='P101', name='Transient Perfume')
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    stock = Stock(product_id=prod.id, product_name=prod.name, quantity_stock=5)
    db_session.add(stock)
    etag = Etagere(etagere_code='E11', depot_id=1, product_id=prod.id, name='ShelfT', quantity_etagere=1)
    db_session.add(etag)
    db_session.commit()

    svc = RemovalWatchService(timeout_minutes=2)
    watch = svc.upsert_presence(db_session, 'E11', prod.id, count=1)

    # Simulate almost expired, then new presence
    watch.last_seen = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=1, seconds=50)
    db_session.commit()

    # New presence resets last_seen
    svc.upsert_presence(db_session, 'E11', prod.id, count=1)

    # process; should not process because last_seen recent
    svc.process_expired_watches(db_session)

    a = db_session.query(Alert).filter(Alert.product_id == prod.id).first()
    assert a is None


def test_processed_watch_not_reprocessed(db_session):
    prod = Product(product_code='P102', name='OnceOnly Perfume')
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    stock = Stock(product_id=prod.id, product_name=prod.name, quantity_stock=3)
    db_session.add(stock)
    etag = Etagere(etagere_code='E12', depot_id=1, product_id=prod.id, name='ShelfO', quantity_etagere=1)
    db_session.add(etag)
    db_session.commit()

    svc = RemovalWatchService(timeout_minutes=2)
    watch = svc.upsert_presence(db_session, 'E12', prod.id, count=1)

    # expire and process once
    watch.last_seen = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(minutes=5)
    db_session.commit()
    svc.process_expired_watches(db_session)

    first_alerts = db_session.query(Alert).filter(Alert.product_id == prod.id).all()
    assert len(first_alerts) == 1

    # process again; should not create another alert
    svc.process_expired_watches(db_session)
    second_alerts = db_session.query(Alert).filter(Alert.product_id == prod.id).all()
    assert len(second_alerts) == 1
