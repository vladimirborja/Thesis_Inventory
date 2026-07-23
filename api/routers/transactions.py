"""
api/routers/transactions.py — Stock Transactions (stock-in, stock-out, adjustment, transfer)
Automatically adjusts product.quantity on every transaction.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, log_activity
from api.models import StockTransaction, Product, Warehouse, Supplier, User
from api.schemas import TransactionCreate, TransactionResponse

router = APIRouter()


def _enrich(tx: StockTransaction) -> TransactionResponse:
    data = TransactionResponse.model_validate(tx)
    data.product_name   = tx.product.name if tx.product else None
    data.warehouse_name = tx.warehouse.name if tx.warehouse else None
    data.supplier_name  = tx.supplier.name if tx.supplier else None
    data.user_name      = tx.user.name if tx.user else None
    return data


@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    search:     Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = (
        db.query(StockTransaction)
        .join(Product, StockTransaction.product_id == Product.id)
        .join(User,    StockTransaction.user_id    == User.id)
        .outerjoin(Warehouse, StockTransaction.warehouse_id == Warehouse.id)
        .outerjoin(Supplier,  StockTransaction.supplier_id  == Supplier.id)
        .order_by(StockTransaction.created_at.desc())
    )
    if type_filter:
        q = q.filter(StockTransaction.type == type_filter)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Product.name.ilike(term)
            | StockTransaction.reference_number.ilike(term)
            | User.name.ilike(term)
        )
    return [_enrich(tx) for tx in q.all()]


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    body: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Calculate quantity delta
    if body.type == "stock-in":
        delta = body.quantity
    elif body.type == "stock-out":
        if product.quantity < body.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        delta = -body.quantity
    elif body.type == "adjustment":
        delta = body.quantity          # can be negative (caller controls sign)
    elif body.type == "transfer":
        if product.quantity < body.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for transfer")
        delta = 0                      # transfer doesn't change total quantity
    else:
        delta = 0

    product.quantity += delta

    tx = StockTransaction(
        product_id=body.product_id,
        warehouse_id=body.warehouse_id,
        supplier_id=body.supplier_id,
        user_id=current_user.id,
        type=body.type,
        quantity=body.quantity,
        reference_number=body.reference_number,
        notes=body.notes,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    log_activity(db, current_user.id, f"tx-{body.type}", {
        "product_id": body.product_id,
        "qty": body.quantity,
        "ref": body.reference_number,
    })
    db.commit()
    return _enrich(tx)
