"""
api/routers/dashboard.py — Super Admin summary aggregates
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_super_admin
from api.models import User, Sale, StockTransaction, Product
from api.schemas import DashboardSummaryResponse

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0

    # Purchase / stock-in value ≈ qty received × product cost price
    total_buy = (
        db.query(func.coalesce(func.sum(StockTransaction.quantity * Product.cost_price), 0))
        .join(Product, StockTransaction.product_id == Product.id)
        .filter(StockTransaction.type == "stock-in")
        .scalar()
    )
    total_buy = float(total_buy or 0)

    total_sell = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).scalar()
    total_sell = float(total_sell or 0)

    return DashboardSummaryResponse(
        total_users=total_users,
        total_buy=round(total_buy, 2),
        total_sell=round(total_sell, 2),
    )
