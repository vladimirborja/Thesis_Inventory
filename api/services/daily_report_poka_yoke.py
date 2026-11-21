"""
Poka-Yoke helpers for Duque daily transaction reports (real-money safe).

- Unit prices come from the Excel catalog — never invented
- When a unit price exists, sales (peso) = qty × unit price (server-locked)
- Line total = peso/bundle + peso/piece (server-locked)
- Submitted cash must match counted denominations
- Balance = Total Sales − Cash − Checks − Credit − Expenses
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException

from api.schemas import CashDenominationCreate, DailyReportCreate, DailyReportItemCreate
from api.services.daily_report_template import calc_denom_total
from api.services.product_catalog import DUQUE_PRODUCT_CATALOG

TOLERANCE = Decimal("0.01")
HIST_TAG = "historical-import"


def money(value: float | int | Decimal | None) -> float:
    """Round half-up to 2 decimal places (cash-safe)."""
    d = Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d)


def _price_index() -> Dict[str, Tuple[float, float]]:
    """Map product_name(lower) → (bundle_price, piece_price) from Excel catalog."""
    out: Dict[str, Tuple[float, float]] = {}
    for name, _sku, _wt, bundle, piece in DUQUE_PRODUCT_CATALOG:
        out[name.strip().lower()] = (float(bundle or 0), float(piece or 0))
    return out


PRICE_BY_NAME = _price_index()


def resolve_unit_prices(product_name: str) -> Tuple[Optional[float], Optional[float]]:
    bundle, piece = PRICE_BY_NAME.get(product_name.strip().lower(), (0.0, 0.0))
    return (bundle if bundle > 0 else None, piece if piece > 0 else None)


def lock_item_pesos(item: DailyReportItemCreate) -> DailyReportItemCreate:
    """
    If Excel unit price exists, peso sales are qty × price (authoritative).
    If no unit price, keep operator-entered peso amounts.
    """
    pb, pp = resolve_unit_prices(item.product_name)
    updates = {}

    if pb is not None and item.sales_bundle is not None:
        updates["sales_peso_bundle"] = money(Decimal(str(item.sales_bundle)) * Decimal(str(pb)))
    elif item.sales_peso_bundle is not None:
        updates["sales_peso_bundle"] = money(item.sales_peso_bundle)

    if pp is not None and item.sales_piece is not None:
        updates["sales_peso_piece"] = money(Decimal(str(item.sales_piece)) * Decimal(str(pp)))
    elif item.sales_peso_piece is not None:
        updates["sales_peso_piece"] = money(item.sales_peso_piece)

    locked = item.model_copy(update=updates) if updates else item
    total = money(
        Decimal(str(locked.sales_peso_bundle or 0)) + Decimal(str(locked.sales_peso_piece or 0))
    )
    return locked.model_copy(update={"total_sales": total})


def recompute_items(items: List[DailyReportItemCreate]) -> Tuple[List[DailyReportItemCreate], float]:
    recomputed = [lock_item_pesos(item) for item in items]
    grand = money(sum(Decimal(str(i.total_sales or 0)) for i in recomputed))
    return recomputed, grand


def calc_balance(
    total_sales: float,
    cash: float,
    checks: float,
    credit: float,
    expenses: float,
) -> float:
    return money(
        Decimal(str(total_sales))
        - Decimal(str(cash))
        - Decimal(str(checks))
        - Decimal(str(credit))
        - Decimal(str(expenses))
    )


def denom_total_from(body_denoms: CashDenominationCreate) -> float:
    return money(
        calc_denom_total(
            body_denoms.bill_1000,
            body_denoms.bill_500,
            body_denoms.bill_200,
            body_denoms.bill_100,
            body_denoms.bill_50,
            body_denoms.bill_20,
            body_denoms.coins,
        )
    )


def validate_submitted_rows(items: List[DailyReportItemCreate]) -> None:
    errors: List[str] = []
    for i, item in enumerate(items, start=1):
        label = f"{item.product_name}" + (f" ({item.weight})" if item.weight else "")
        # Only require fields on rows that moved stock or recorded sales
        has_activity = any(
            [
                (item.load_in or "").strip() not in ("", "0"),
                (item.load_out_bundle or "").strip() not in ("", "0"),
                (item.load_out_piece or 0) not in (None, 0),
                (item.sales_bundle or 0) not in (None, 0),
                (item.sales_piece or 0) not in (None, 0),
                (item.sales_peso_bundle or 0) not in (None, 0),
                (item.sales_peso_piece or 0) not in (None, 0),
                (item.total_sales or 0) not in (None, 0),
            ]
        )
        if not has_activity:
            continue

        if item.load_in is None or str(item.load_in).strip() == "":
            errors.append(f'Row {i} "{label}": Load-in required')
        if item.load_out_bundle is None or str(item.load_out_bundle).strip() == "":
            errors.append(f'Row {i} "{label}": Load-out/Bdl required')
        if item.sales_bundle is None and item.sales_piece is None:
            errors.append(f'Row {i} "{label}": Sales qty (bundle or piece) required')

        pb, pp = resolve_unit_prices(item.product_name)
        if pb is not None and item.sales_bundle is not None:
            expected = money(Decimal(str(item.sales_bundle)) * Decimal(str(pb)))
            actual = money(item.sales_peso_bundle or 0)
            if abs(Decimal(str(expected)) - Decimal(str(actual))) > TOLERANCE:
                errors.append(
                    f'Row {i} "{label}": ₱/bundle must be {expected} '
                    f"({item.sales_bundle} × ₱{pb})"
                )
        if pp is not None and item.sales_piece is not None:
            expected = money(Decimal(str(item.sales_piece)) * Decimal(str(pp)))
            actual = money(item.sales_peso_piece or 0)
            if abs(Decimal(str(expected)) - Decimal(str(actual))) > TOLERANCE:
                errors.append(
                    f'Row {i} "{label}": ₱/piece must be {expected} '
                    f"({item.sales_piece} × ₱{pp})"
                )

    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Report blocked — fix money/quantity fields before submitting.",
                "errors": errors[:25],
                "error_count": len(errors),
            },
        )


def apply_poka_yoke(body: DailyReportCreate) -> Tuple[DailyReportCreate, float, float]:
    """
    Returns (normalized_body, total_sales, denom_total).
    Server is the source of truth for pesos, cash, and balance.
    """
    items, total_sales = recompute_items(body.items)
    denom_total = denom_total_from(body.denominations)
    is_historical = HIST_TAG in (body.notes or "")

    if body.status == "submitted":
        validate_submitted_rows(items)

        if denom_total > 0:
            # Counted bills/coins are the only trusted cash figure
            cash = denom_total
        elif is_historical and float(body.cash_collection or 0) > 0:
            # Excel Jan–Jul imports recorded cash without denomination sheets
            cash = money(body.cash_collection)
        elif float(body.cash_collection or 0) > 0 and denom_total == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Cash collection requires bill/coin count (Poka-Yoke).",
                    "errors": [
                        "Enter denominations so Cash = counted total. "
                        "Do not type cash by hand for live reports."
                    ],
                    "error_count": 1,
                },
            )
        else:
            cash = 0.0
    else:
        # Draft: prefer denom when counted; otherwise keep entered cash
        cash = denom_total if denom_total > 0 else money(body.cash_collection)

    checks = money(body.checks_collection)
    credit = money(body.credit_sales)
    expenses = money(body.expenses)
    balance = calc_balance(total_sales, cash, checks, credit, expenses)

    normalized = body.model_copy(
        update={
            "items": items,
            "cash_collection": cash,
            "checks_collection": checks,
            "credit_sales": credit,
            "expenses": expenses,
            "balance": balance,
        }
    )
    return normalized, total_sales, denom_total
