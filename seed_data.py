# -*- coding: utf-8 -*-
"""
seed_data.py
============
Seeds ALL tables with 10 realistic rows each.
Tables are populated in dependency order:
  1. users
  2. products
  3. depot
  4. etagere       (refs: depot, products)
  5. stock         (refs: products)
  6. transfers     (refs: products)
  7. alerts        (refs: products, stock, etagere, depot)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal
from app.models.user      import User, UserRole
from app.models.product   import Product
from app.models.depot     import Depot
from app.models.etagere   import Etagere
from app.models.stock     import Stock
from app.models.transfer  import Transfer
from app.models.alert     import Alert
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(pw: str) -> str:
    return pwd_ctx.hash(pw)

# ──────────────────────────────────────────────────────────────────────────────
def seed_users(db):
    rows = [
        User(username="chef_depot1",    email="chef1@stock.tn",   password_hash=hash_pw("Chef1Pass!"),     full_name="Ahmed Bouaziz",     role=UserRole.ADMIN,       is_active=True),
        User(username="resp_zone_a",    email="resp_a@stock.tn",  password_hash=hash_pw("RespA1Pass!"),    full_name="Sara Mejri",        role=UserRole.RESPONSIBLE, is_active=True),
        User(username="resp_zone_b",    email="resp_b@stock.tn",  password_hash=hash_pw("RespB2Pass!"),    full_name="Karim Dridi",       role=UserRole.RESPONSIBLE, is_active=True),
        User(username="superviseur1",   email="sup1@stock.tn",    password_hash=hash_pw("Sup1Pass!"),      full_name="Fatma Khalil",      role=UserRole.ADMIN,       is_active=True),
        User(username="operateur1",     email="op1@stock.tn",     password_hash=hash_pw("Op1Pass!"),       full_name="Mohamed Trabelsi",  role=UserRole.RESPONSIBLE, is_active=True),
        User(username="operateur2",     email="op2@stock.tn",     password_hash=hash_pw("Op2Pass!"),       full_name="Amira Karray",      role=UserRole.RESPONSIBLE, is_active=True),
        User(username="logisticien1",   email="log1@stock.tn",    password_hash=hash_pw("Log1Pass!"),      full_name="Yassine Mansour",   role=UserRole.RESPONSIBLE, is_active=True),
        User(username="auditeur1",      email="audit1@stock.tn",  password_hash=hash_pw("Audit1Pass!"),    full_name="Rania Ferjani",     role=UserRole.ADMIN,       is_active=True),
        User(username="magasinier1",    email="mag1@stock.tn",    password_hash=hash_pw("Mag1Pass!"),      full_name="Bilel Hamdi",       role=UserRole.RESPONSIBLE, is_active=True),
        User(username="magasinier2",    email="mag2@stock.tn",    password_hash=hash_pw("Mag2Pass!"),      full_name="Nour Zouari",       role=UserRole.RESPONSIBLE, is_active=True),
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Users: {len(rows)} rows inserted")
    return rows


def seed_products(db):
    rows = [
        Product(product_code="PROD-001", name="Lait demi-écrémé 1L",   category="Produits laitiers",   price=1.50, unit="L",    description="Lait pasteurisé demi-écrémé en bouteille 1 litre"),
        Product(product_code="PROD-002", name="Eau minérale 1.5L",     category="Boissons",            price=0.80, unit="L",    description="Eau minérale naturelle en bouteille plastique"),
        Product(product_code="PROD-003", name="Farine de blé 1kg",     category="Épicerie",            price=1.20, unit="kg",   description="Farine de blé tout usage type 55"),
        Product(product_code="PROD-004", name="Sucre blanc 1kg",       category="Épicerie",            price=1.10, unit="kg",   description="Sucre cristallisé blanc"),
        Product(product_code="PROD-005", name="Huile végétale 1L",     category="Épicerie",            price=2.30, unit="L",    description="Huile de tournesol raffinée"),
        Product(product_code="PROD-006", name="Riz basmati 1kg",       category="Céréales",            price=2.50, unit="kg",   description="Riz basmati à grains longs"),
        Product(product_code="PROD-007", name="Pâtes alimentaires 500g", category="Céréales",          price=0.90, unit="pcs",  description="Pâtes de semoule de blé dur"),
        Product(product_code="PROD-008", name="Tomate en conserve 400g", category="Conserves",         price=1.40, unit="pcs",  description="Tomates pelées en jus de tomate"),
        Product(product_code="PROD-009", name="Thon en boîte 160g",    category="Conserves",           price=2.10, unit="pcs",  description="Thon entier à l'huile d'olive"),
        Product(product_code="PROD-010", name="Café moulu 250g",       category="Boissons chaudes",    price=4.50, unit="pcs",  description="Café arabica moulu pour cafetière filtre"),
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Products: {len(rows)} rows inserted")
    return rows


def seed_depots(db):
    rows = [
        Depot(depot_code="DEP-A1", name="Entrepôt Central A",   location="Zone Industrielle, Tunis",     manager_name="Ahmed Bouaziz",    phone="71 234 567", quantity_depot=500),
        Depot(depot_code="DEP-B1", name="Dépôt Nord Tunis",     location="La Marsa, Tunis",              manager_name="Sara Mejri",       phone="71 345 678", quantity_depot=320),
        Depot(depot_code="DEP-C1", name="Dépôt Sfax",           location="Route de Gabès, Sfax",         manager_name="Karim Dridi",      phone="74 456 789", quantity_depot=410),
        Depot(depot_code="DEP-D1", name="Dépôt Sousse",         location="Zone Commerciale, Sousse",     manager_name="Fatma Khalil",     phone="73 567 890", quantity_depot=280),
        Depot(depot_code="DEP-E1", name="Dépôt Monastir",       location="Aéroport de Monastir",         manager_name="Mohamed Trabelsi", phone="73 678 901", quantity_depot=190),
        Depot(depot_code="DEP-F1", name="Entrepôt Frigorifique", location="Zone Portuaire, Tunis",       manager_name="Amira Karray",     phone="71 789 012", quantity_depot=150),
        Depot(depot_code="DEP-G1", name="Dépôt Nabeul",         location="Route Touristique, Nabeul",    manager_name="Yassine Mansour",  phone="72 890 123", quantity_depot=220),
        Depot(depot_code="DEP-H1", name="Dépôt Bizerte",        location="Port de Bizerte",              manager_name="Rania Ferjani",    phone="72 901 234", quantity_depot=310),
        Depot(depot_code="DEP-I1", name="Dépôt Kairouan",       location="Zone Artisanale, Kairouan",    manager_name="Bilel Hamdi",      phone="77 012 345", quantity_depot=180),
        Depot(depot_code="DEP-J1", name="Dépôt Béja",           location="Route de Jendouba, Béja",      manager_name="Nour Zouari",      phone="78 123 456", quantity_depot=240),
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Depots: {len(rows)} rows inserted")
    return rows


def seed_etageres(db, depots, products):
    rows = [
        Etagere(etagere_code="ETG-A01", depot_id=depots[0].id, product_id=products[0].id, name="Rayon Laitier A",      section="A", quantity_etagere=80,  max_capacity=150),
        Etagere(etagere_code="ETG-A02", depot_id=depots[0].id, product_id=products[1].id, name="Rayon Boissons A",     section="A", quantity_etagere=120, max_capacity=200),
        Etagere(etagere_code="ETG-B01", depot_id=depots[1].id, product_id=products[2].id, name="Rayon Farine B",       section="B", quantity_etagere=60,  max_capacity=100),
        Etagere(etagere_code="ETG-B02", depot_id=depots[1].id, product_id=products[3].id, name="Rayon Sucre B",        section="B", quantity_etagere=40,  max_capacity=100),
        Etagere(etagere_code="ETG-C01", depot_id=depots[2].id, product_id=products[4].id, name="Rayon Huiles C",       section="C", quantity_etagere=70,  max_capacity=120),
        Etagere(etagere_code="ETG-C02", depot_id=depots[2].id, product_id=products[5].id, name="Rayon Céréales C",     section="C", quantity_etagere=90,  max_capacity=150),
        Etagere(etagere_code="ETG-D01", depot_id=depots[3].id, product_id=products[6].id, name="Rayon Pâtes D",        section="D", quantity_etagere=15,  max_capacity=100),
        Etagere(etagere_code="ETG-D02", depot_id=depots[3].id, product_id=products[7].id, name="Rayon Conserves D",    section="D", quantity_etagere=10,  max_capacity=80),
        Etagere(etagere_code="ETG-E01", depot_id=depots[4].id, product_id=products[8].id, name="Rayon Thon E",         section="E", quantity_etagere=5,   max_capacity=60),
        Etagere(etagere_code="ETG-E02", depot_id=depots[4].id, product_id=products[9].id, name="Rayon Café E",         section="E", quantity_etagere=50,  max_capacity=80),
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Etageres: {len(rows)} rows inserted")
    return rows


def seed_stock(db, products):
    rows = [
        Stock(product_id=products[0].id, product_name=products[0].name, barcode="6191234560001", quantity_stock=200),
        Stock(product_id=products[1].id, product_name=products[1].name, barcode="6191234560002", quantity_stock=350),
        Stock(product_id=products[2].id, product_name=products[2].name, barcode="6191234560003", quantity_stock=180),
        Stock(product_id=products[3].id, product_name=products[3].name, barcode="6191234560004", quantity_stock=220),
        Stock(product_id=products[4].id, product_name=products[4].name, barcode="6191234560005", quantity_stock=140),
        Stock(product_id=products[5].id, product_name=products[5].name, barcode="6191234560006", quantity_stock=310),
        Stock(product_id=products[6].id, product_name=products[6].name, barcode="6191234560007", quantity_stock=90),
        Stock(product_id=products[7].id, product_name=products[7].name, barcode="6191234560008", quantity_stock=75),
        Stock(product_id=products[8].id, product_name=products[8].name, barcode="6191234560009", quantity_stock=60),
        Stock(product_id=products[9].id, product_name=products[9].name, barcode="6191234560010", quantity_stock=130),
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Stock: {len(rows)} rows inserted")
    return rows


def seed_transfers(db, products):
    locations = ['stock', 'depot', 'etagere']
    pairs = [
        ('stock',   'depot'),
        ('depot',   'etagere'),
        ('stock',   'etagere'),
        ('etagere', 'depot'),
        ('depot',   'stock'),
        ('stock',   'depot'),
        ('etagere', 'stock'),
        ('depot',   'etagere'),
        ('stock',   'etagere'),
        ('depot',   'stock'),
    ]
    rows = [
        Transfer(product_id=products[i].id, product_name=products[i].name,
                 from_location=pairs[i][0], to_location=pairs[i][1],
                 quantity=(i+1)*10,
                 notes=f"Transfert réf. TR-{2024+i:04d} – réapprovisionnement de routine")
        for i in range(10)
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Transfers: {len(rows)} rows inserted")
    return rows


def seed_alerts(db, products, stocks, etageres, depots):
    alert_types = ['missing', 'box_missing', 'low_stock', 'overstock', 'missing',
                   'box_missing', 'low_stock', 'missing', 'low_stock', 'box_missing']
    rows = [
        Alert(
            product_id        = products[i].id,
            product_name      = products[i].name,
            alert_type        = alert_types[i],
            expected_quantity = (i+1) * 20,
            actual_quantity   = (i+1) * 10,
            difference        = (i+1) * 10,
            message           = f"Alerte {alert_types[i]} : quantité insuffisante pour {products[i].name}",
            quantity_stock    = stocks[i].quantity_stock,
            quantity_etagere  = etageres[i].quantity_etagere,
            quantity_depot    = depots[i].quantity_depot,
            boxes_missing_count = i % 5,
            timeout_minutes   = 5,
            stock_id          = stocks[i].id,
            etagere_id        = etageres[i].id,
            depot_id          = depots[i].id,
            etagere_code      = etageres[i].etagere_code,
        )
        for i in range(10)
    ]
    db.add_all(rows)
    db.flush()
    print(f"  [OK] Alerts: {len(rows)} rows inserted")
    return rows


# ──────────────────────────────────────────────────────────────────────────────
def main():
    db = SessionLocal()
    try:
        print("\n[SEED]  Seeding database...\n")

        users    = seed_users(db)
        products = seed_products(db)
        depots   = seed_depots(db)
        etageres = seed_etageres(db, depots, products)
        stocks   = seed_stock(db, products)
        _        = seed_transfers(db, products)
        _        = seed_alerts(db, products, stocks, etageres, depots)

        db.commit()
        print("\n[OK]  All tables seeded successfully!\n")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR]  {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
