"""
seed_alerts.py — Crée 6 alertes de test basées sur les produits existants en étagère
"""
from app.db import SessionLocal
from app.models.etagere import Etagere
from app.models.product import Product
from app.models.stock import Stock
from app.models.depot import Depot
from app.services.alert_service import AlertService
from datetime import datetime

def list_etageres():
    db = SessionLocal()
    try:
        etageres = db.query(Etagere).all()
        print(f"\n{'='*60}")
        print(f"  ETAGERES TROUVEES : {len(etageres)}")
        print(f"{'='*60}")
        for e in etageres:
            prod = db.query(Product).filter(Product.id == e.product_id).first() if e.product_id else None
            print(f"  ID={e.id} | code={e.etagere_code} | qty={e.quantity_etagere} | produit={prod.name if prod else 'Aucun'}")
        print(f"{'='*60}\n")
        return etageres
    finally:
        db.close()

def seed_alerts():
    db = SessionLocal()
    alert_service = AlertService()
    
    try:
        # Only use étagères that have a product linked
        all_etageres = db.query(Etagere).all()
        etageres = [e for e in all_etageres if e.product_id and e.product_id > 0][:6]
        
        if not etageres:
            print("ERREUR: Aucune étagère avec un produit trouvée dans la DB.")
            print("Lance d'abord: python seed_db.py")
            return
        
        print(f"  {len(etageres)} étagère(s) avec produit(s) trouvée(s). Création des alertes...")
        
        created = 0
        for i, etagere in enumerate(etageres):
            prod = db.query(Product).filter(Product.id == etagere.product_id).first()
            if not prod:
                print(f"  ⚠️  Étagère {etagere.etagere_code}: produit id={etagere.product_id} introuvable, ignorée.")
                continue
            stock = db.query(Stock).filter(Stock.product_id == prod.id).first()
            depot = db.query(Depot).filter(Depot.id == etagere.depot_id).first() if etagere.depot_id else None
            
            product_name = prod.name
            product_id   = prod.id
            qty_etagere  = etagere.quantity_etagere or 5
            qty_stock    = stock.quantity_stock if stock else 0
            qty_depot    = depot.quantity_depot  if depot else 0
            
            # Alterner entre type 'missing' et 'box_missing'
            if i % 2 == 0:
                # Alerte MISSING — étagère vide
                alert_type = "missing"
                actual_qty = 0
                expected_qty = qty_etagere
                boxes_missing = expected_qty
                message = (
                    f"L'étagère {etagere.name} ({etagere.etagere_code}) est vide. "
                    f"Le produit \"{product_name}\" est introuvable à la caméra."
                )
            else:
                # Alerte BOX_MISSING — boîte(s) manquante(s)
                missing_count = max(1, qty_etagere // 3)  # 1/3 des boîtes manquantes
                alert_type = "box_missing"
                actual_qty = qty_etagere - missing_count
                expected_qty = qty_etagere
                boxes_missing = missing_count
                message = (
                    f"{missing_count} boîte(s) de \"{product_name}\" manquante(s) "
                    f"depuis l'étagère {etagere.name} ({etagere.etagere_code}) depuis 5 minutes."
                )
            
            alert = alert_service.create_alert(
                db=db,
                product_id=product_id,
                product_name=product_name,
                alert_type=alert_type,
                expected_quantity=expected_qty,
                actual_quantity=actual_qty,
                message=message,
                quantity_stock=qty_stock,
                quantity_etagere=actual_qty,
                quantity_depot=qty_depot,
                stock_id=stock.id if stock else None,
                etagere_id=etagere.id,
                depot_id=etagere.depot_id,
                boxes_missing_count=boxes_missing,
                state_change_time=datetime.now(),
                timeout_minutes=5,
                etagere_code=etagere.etagere_code,
            )
            created += 1
            print(f"  ✅ Alerte #{alert.id} créée | type={alert_type} | produit={product_name} | étagère={etagere.etagere_code}")
        
        print(f"\n{'='*60}")
        print(f"  {created} ALERTES CREEES AVEC SUCCES")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback; traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    list_etageres()
    seed_alerts()
