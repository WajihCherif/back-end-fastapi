import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, engine, SessionLocal
from app.models.product import Product
from app.models.stock import Stock
from app.models.depot import Depot
from app.models.etagere import Etagere
import random

def seed():
    db = SessionLocal()
    
    # Perfumes from YOLO + 4 extra to make it 10
    perfumes = [
        "KHAMRAH", "MEN_Parfulux", "Royal_Ramba", "ZARA", "salvage", "scandal_h",
        "Dior_Sauvage", "Bleu_de_Chanel", "Versace_Eros", "Tom_Ford_Oud_Wood"
    ]
    
    try:
        # Create Depot
        depot = db.query(Depot).filter(Depot.depot_code == "DEP-01").first()
        if not depot:
            depot = Depot(
                depot_code="DEP-01",
                name="Main Perfume Depot",
                location="Tunis Center",
                address="123 Perfume Street",
                manager_name="Wajih",
                phone="12345678",
                quantity_depot=1000
            )
            db.add(depot)
            db.commit()
            db.refresh(depot)
            
        for i, name in enumerate(perfumes):
            # Create Product
            prod = db.query(Product).filter(Product.product_code == f"PRF-00{i}").first()
            if not prod:
                prod = Product(
                    product_code=f"PRF-00{i}",
                    name=name,
                    description=f"High quality perfume: {name}",
                    category="Perfume",
                    price=random.uniform(50.0, 300.0),
                    unit="piece"
                )
                db.add(prod)
                db.commit()
                db.refresh(prod)
            
            # Create Stock
            stock = db.query(Stock).filter(Stock.product_id == prod.id).first()
            if not stock:
                stock = Stock(
                    product_id=prod.id,
                    product_name=prod.name,
                    barcode=f"BAR-{prod.product_code}",
                    quantity_stock=random.randint(10, 100)
                )
                db.add(stock)
                db.commit()
                
            # Create Etagere
            etagere = db.query(Etagere).filter(Etagere.etagere_code == f"ETG-{i}").first()
            if not etagere:
                etagere = Etagere(
                    etagere_code=f"ETG-{i}",
                    depot_id=depot.id,
                    product_id=prod.id,
                    name=f"Shelf {name}",
                    section=f"Section {chr(65+i)}",
                    quantity_etagere=random.randint(5, 50),
                    max_capacity=100
                )
                db.add(etagere)
                db.commit()
                
        print("Successfully seeded 10 products in all tables!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
