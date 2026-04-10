from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.depot import DepotCreate, DepotUpdate, DepotResponse
from app.services.depot_service import DepotService

router = APIRouter(prefix="/depots", tags=["Depots"])
depot_service = DepotService()

@router.post("/", response_model=DepotResponse, status_code=201)
def create_depot(
    depot: DepotCreate,
    db: Session = Depends(get_db)
):
    try:
        return depot_service.create_depot(db, depot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DepotResponse])
def get_depots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return depot_service.get_depots(db, skip=skip, limit=limit, search=search)

@router.get("/{depot_id}", response_model=DepotResponse)
def get_depot(
    depot_id: int,
    db: Session = Depends(get_db)
):
    depot = depot_service.get_depot(db, depot_id)
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot

@router.get("/by-code/{depot_code}", response_model=DepotResponse)
def get_depot_by_code(
    depot_code: str,
    db: Session = Depends(get_db)
):
    depot = depot_service.get_depot_by_code(db, depot_code)
    if not depot:
        raise HTTPException(status_code=404, detail="Depot not found")
    return depot

@router.put("/{depot_id}", response_model=DepotResponse)
def update_depot(
    depot_id: int,
    depot_update: DepotUpdate,
    db: Session = Depends(get_db)
):
    try:
        depot = depot_service.update_depot(db, depot_id, depot_update)
        if not depot:
            raise HTTPException(status_code=404, detail="Depot not found")
        return depot
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{depot_id}", status_code=204)
def delete_depot(
    depot_id: int,
    db: Session = Depends(get_db)
):
    success = depot_service.delete_depot(db, depot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Depot not found")
    return None
