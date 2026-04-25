from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.etagere import EtagereCreate, EtagereUpdate, EtagereResponse, EtagereDetailResponse
from app.services.etagere_service import EtagereService

router = APIRouter(prefix="/etageres", tags=["Etageres"])
etagere_service = EtagereService()

@router.post("/", response_model=EtagereResponse, status_code=201)
def create_etagere(
    etagere: EtagereCreate,
    db: Session = Depends(get_db)
):
    try:
        return etagere_service.create_etagere(db, etagere)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[EtagereResponse])
def get_etageres(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    depot_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return etagere_service.get_etageres(db, skip=skip, limit=limit, depot_id=depot_id, search=search)

@router.get("/details", response_model=List[EtagereDetailResponse])
def get_etageres_with_details(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    depot_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    etageres = etagere_service.get_etageres(db, skip=skip, limit=limit, depot_id=depot_id, search=None)
    result = []
    for etagere in etageres:
        details = etagere_service.get_etagere_details(db, etagere.id)
        if details:
            result.append(details)
    return result

@router.get("/{etagere_id}", response_model=EtagereResponse)
def get_etagere(
    etagere_id: int,
    db: Session = Depends(get_db)
):
    etagere = etagere_service.get_etagere(db, etagere_id)
    if not etagere:
        raise HTTPException(status_code=404, detail="Etagere not found")
    return etagere

@router.get("/by-code/{etagere_code}", response_model=EtagereDetailResponse)
def get_etagere_by_code(
    etagere_code: str,
    db: Session = Depends(get_db)
):
    details = etagere_service.get_etagere_details_by_code(db, etagere_code)
    if not details:
        raise HTTPException(status_code=404, detail="Etagere not found")
    return details

@router.put("/{etagere_id}", response_model=EtagereResponse)
def update_etagere(
    etagere_id: int,
    etagere_update: EtagereUpdate,
    db: Session = Depends(get_db)
):
    try:
        etagere = etagere_service.update_etagere(db, etagere_id, etagere_update)
        if not etagere:
            raise HTTPException(status_code=404, detail="Etagere not found")
        return etagere
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{etagere_code}/stock")
def update_stock(
    etagere_code: str,
    quantity: int = Query(..., ge=0),
    db: Session = Depends(get_db)
):
    etagere = etagere_service.update_stock(db, etagere_code, quantity)
    if not etagere:
        raise HTTPException(status_code=404, detail="Etagere not found")
    return {"message": "Stock updated", "etagere_code": etagere_code, "new_quantity": etagere.quantity_etagere}

@router.post("/{etagere_code}/restock")
def restock_etagere(
    etagere_code: str,
    db: Session = Depends(get_db)
):
    etagere = etagere_service.restock_etagere(db, etagere_code)
    if not etagere:
        raise HTTPException(status_code=404, detail="Etagere not found")
    return {"message": "Etagere restocked", "etagere_code": etagere_code, "quantity": etagere.quantity_etagere}

@router.delete("/{etagere_id}", status_code=204)
def delete_etagere(
    etagere_id: int,
    db: Session = Depends(get_db)
):
    success = etagere_service.delete_etagere(db, etagere_id)
    if not success:
        raise HTTPException(status_code=404, detail="Etagere not found")
    return None
