"""
api/routers/suppliers.py
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, require_admin, log_activity
from api.models import Supplier, User
from api.schemas import SupplierCreate, SupplierResponse, SupplierUpdate

router = APIRouter()


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [SupplierResponse.model_validate(s) for s in db.query(Supplier).order_by(Supplier.name).all()]


@router.post("", response_model=SupplierResponse, status_code=201)
def create_supplier(
    body: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    supplier = Supplier(**body.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    log_activity(db, current_user.id, "supplier-create", {"name": body.name})
    db.commit()
    return SupplierResponse.model_validate(supplier)


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse.model_validate(s)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    log_activity(db, current_user.id, "supplier-update", {"id": supplier_id})
    db.commit()
    return SupplierResponse.model_validate(s)


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(s)
    db.commit()
    log_activity(db, current_user.id, "supplier-delete", {"id": supplier_id})
    db.commit()
