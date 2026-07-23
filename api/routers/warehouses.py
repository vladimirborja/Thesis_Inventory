"""
api/routers/warehouses.py
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user
from api.models import Warehouse, User
from api.schemas import WarehouseResponse

router = APIRouter()


@router.get("", response_model=List[WarehouseResponse])
def list_warehouses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [WarehouseResponse.model_validate(w) for w in db.query(Warehouse).order_by(Warehouse.name).all()]
