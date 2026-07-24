"""
api/routers/analytics.py — Demand forecast, ABC analysis, ROP / safety stock.
Admin + Super Admin only.
"""

from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_admin
from api.models import Product, Sale, SaleItem, Ingredient, ProductIngredient, User
from api.schemas import (
    ProductForecastResponse,
    ForecastHistoryPoint,
    ForecastPoint,
    AbcAnalysisResponse,
    AbcItem,
    ReorderPointItem,
    AnalyticsOverviewResponse,
)
from api.services.forecasting import forecast_product_demand
from api.services.abc_analysis import classify_abc, abc_summary
from api.services.reorder import (
    daily_usage_series,
    compute_rop,
    DEFAULT_LEAD_TIME_DAYS,
    DEFAULT_Z,
    DEFAULT_LOOKBACK_DAYS,
)

router = APIRouter()


def _sale_qty_rows(db: Session, product_id: int) -> List[tuple]:
    rows = (
        db.query(Sale.created_at, SaleItem.quantity)
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .filter(SaleItem.product_id == product_id)
        .all()
    )
    return [(r[0], float(r[1])) for r in rows]


def _ingredient_usage_rows(db: Session, ingredient_id: int) -> List[tuple]:
    """Derive ingredient demand from finished-good sales × recipe qty."""
    rows = (
        db.query(Sale.created_at, SaleItem.quantity, ProductIngredient.quantity_required)
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .join(ProductIngredient, ProductIngredient.product_id == SaleItem.product_id)
        .filter(ProductIngredient.ingredient_id == ingredient_id)
        .all()
    )
    return [(r[0], float(r[1]) * float(r[2])) for r in rows]


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def analytics_overview(
    lead_time_days: int = Query(DEFAULT_LEAD_TIME_DAYS, ge=1, le=90),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    abc_rows = _build_abc(db)
    counts = abc_summary(abc_rows)

    products = db.query(Product).all()
    below_p = 0
    mapes: List[float] = []
    for p in products:
        rows = _sale_qty_rows(db, p.id)
        daily = daily_usage_series(rows)
        lt = int(getattr(p, "lead_time_days", None) or lead_time_days)
        rop = compute_rop(daily, p.quantity, lt, min_stock_level=p.min_stock_level)
        if rop["below_rop"]:
            below_p += 1
        fc = forecast_product_demand(rows, period="week", horizon=1)
        if fc["mape_percent"] is not None:
            mapes.append(fc["mape_percent"])

    below_i = 0
    for ing in db.query(Ingredient).all():
        rows = _ingredient_usage_rows(db, ing.id)
        daily = daily_usage_series(rows)
        lt = int(getattr(ing, "lead_time_days", None) or lead_time_days)
        rop = compute_rop(
            daily, float(ing.quantity), lt,
            min_stock_level=float(ing.min_stock_level),
        )
        if rop["below_rop"]:
            below_i += 1

    avg_mape = round(sum(mapes) / len(mapes), 2) if mapes else None

    return AnalyticsOverviewResponse(
        products_below_rop=below_p,
        ingredients_below_rop=below_i,
        class_a_count=counts.get("A", 0),
        class_b_count=counts.get("B", 0),
        class_c_count=counts.get("C", 0),
        avg_mape_percent=avg_mape,
        lead_time_days_default=lead_time_days,
    )


@router.get("/forecast/{product_id}", response_model=ProductForecastResponse)
def product_forecast(
    product_id: int,
    period: Literal["week", "month"] = Query("week"),
    horizon: int = Query(4, ge=1, le=12),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = forecast_product_demand(
        _sale_qty_rows(db, product_id),
        period=period,
        horizon=horizon,
    )
    return ProductForecastResponse(
        product_id=product.id,
        product_name=product.name,
        sku=product.sku,
        period=result["period"],
        horizon=result["horizon"],
        method=result["method"],
        alpha=result["alpha"],
        mape_percent=result["mape_percent"],
        next_period_demand=result["next_period_demand"],
        history=[ForecastHistoryPoint(**h) for h in result["history"]],
        forecast=[ForecastPoint(**f) for f in result["forecast"]],
    )


@router.get("/forecast", response_model=List[ProductForecastResponse])
def forecast_all(
    period: Literal["week", "month"] = Query("week"),
    horizon: int = Query(4, ge=1, le=12),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    out: List[ProductForecastResponse] = []
    for product in db.query(Product).order_by(Product.name).all():
        result = forecast_product_demand(
            _sale_qty_rows(db, product.id),
            period=period,
            horizon=horizon,
        )
        out.append(ProductForecastResponse(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            period=result["period"],
            horizon=result["horizon"],
            method=result["method"],
            alpha=result["alpha"],
            mape_percent=result["mape_percent"],
            next_period_demand=result["next_period_demand"],
            history=[ForecastHistoryPoint(**h) for h in result["history"]],
            forecast=[ForecastPoint(**f) for f in result["forecast"]],
        ))
    return out


def _build_abc(db: Session) -> List[dict]:
    value_rows = (
        db.query(
            Product.id,
            Product.name,
            Product.sku,
            func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price), 0),
        )
        .outerjoin(SaleItem, SaleItem.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.sku)
        .all()
    )
    return classify_abc([(r[0], r[1], r[2], float(r[3])) for r in value_rows])


@router.get("/abc", response_model=AbcAnalysisResponse)
def abc_analysis(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    items = _build_abc(db)
    return AbcAnalysisResponse(
        items=[AbcItem(**i) for i in items],
        counts=abc_summary(items),
    )


@router.get("/reorder-points", response_model=List[ReorderPointItem])
def reorder_points(
    lead_time_days: int = Query(DEFAULT_LEAD_TIME_DAYS, ge=1, le=90),
    z: float = Query(DEFAULT_Z, ge=0.5, le=3.5),
    lookback_days: int = Query(DEFAULT_LOOKBACK_DAYS, ge=14, le=365),
    below_rop_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    results: List[ReorderPointItem] = []

    for p in db.query(Product).order_by(Product.name).all():
        daily = daily_usage_series(_sale_qty_rows(db, p.id), lookback_days)
        lt = int(getattr(p, "lead_time_days", None) or lead_time_days)
        calc = compute_rop(
            daily, p.quantity, lt, z, min_stock_level=p.min_stock_level,
        )
        if below_rop_only and not calc["needs_reorder"]:
            continue
        results.append(ReorderPointItem(
            item_type="product",
            item_id=p.id,
            name=p.name,
            sku=p.sku,
            **calc,
        ))

    for ing in db.query(Ingredient).order_by(Ingredient.name).all():
        daily = daily_usage_series(_ingredient_usage_rows(db, ing.id), lookback_days)
        lt = int(getattr(ing, "lead_time_days", None) or lead_time_days)
        calc = compute_rop(
            daily,
            float(ing.quantity),
            lt,
            z,
            min_stock_level=float(ing.min_stock_level),
        )
        if below_rop_only and not calc["needs_reorder"]:
            continue
        results.append(ReorderPointItem(
            item_type="ingredient",
            item_id=ing.id,
            name=ing.name,
            sku=None,
            **calc,
        ))

    results.sort(key=lambda r: (not r.needs_reorder, r.item_type, r.name))
    return results
