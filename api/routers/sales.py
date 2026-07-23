"""
api/routers/sales.py — Record sales; auto-deduct product inventory on commit.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, log_activity
from api.models import Sale, SaleItem, Product, User
from api.schemas import SaleCreate, SaleResponse, SaleItemResponse

router = APIRouter()


def _enrich_sale(sale: Sale) -> SaleResponse:
    data = SaleResponse.model_validate(sale)
    data.user_name = sale.user.name if sale.user else None
    data.items = [
        SaleItemResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            product_name=item.product.name if item.product else None,
        )
        for item in sale.items
    ]
    return data


@router.get("", response_model=List[SaleResponse])
def list_sales(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sales = (
        db.query(Sale)
        .order_by(Sale.created_at.desc())
        .all()
    )
    return [_enrich_sale(s) for s in sales]


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(
    body: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.items:
        raise HTTPException(status_code=400, detail="Sale must have at least one item")

    total = 0.0
    db_items = []

    for item in body.items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product.name}' (available: {product.quantity})",
            )
        # Deduct inventory
        product.quantity -= item.quantity
        
        # Deduct ingredient quantities if mapped
        for link in product.ingredients:
            qty_needed = float(link.quantity_required) * item.quantity
            if float(link.ingredient.quantity) < qty_needed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient ingredient '{link.ingredient.name}' to fulfill sale (available: {link.ingredient.quantity} {link.ingredient.unit or ''})"
                )
            link.ingredient.quantity = float(link.ingredient.quantity) - qty_needed

        line_total = float(item.unit_price) * item.quantity
        total += line_total
        db_items.append(SaleItem(
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        ))

    sale = Sale(
        user_id=current_user.id,
        total_amount=round(total, 2),
        payment_method=body.payment_method,
        notes=body.notes,
        items=db_items,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)

    log_activity(db, current_user.id, "sale", {
        "sale_id": sale.id,
        "total": float(sale.total_amount),
        "items": len(body.items),
    })
    db.commit()

    return _enrich_sale(sale)
