"""
Poka-Yoke helpers for Duque daily transaction reports.

- Recompute line and header totals from source fields (no client math trust)
- Enforce completeness when status == submitted
- Auto-balance: total_sales - cash - checks - credit - expenses
- Cash collection must match denomination total
"""

from __future__ import annotations

from typing import List, Tuple

from fastapi import HTTPException

from api.schemas import CashDenominationCreate, DailyReportCreate, DailyReportItemCreate
from api.services.daily_report_template import calc_denom_total

TOLERANCE = 0.01


def item_total_sales(item: DailyReportItemCreate) -> float:
    return round(
        float(item.sales_peso_bundle or 0) + float(item.sales_peso_piece or 0),
        2,
    )


def recompute_items(items: List[DailyReportItemCreate]) -> Tuple[List[DailyReportItemCreate], float]:
    """Return items with server-locked total_sales and the grand total."""
    recomputed: List[DailyReportItemCreate] = []
    grand = 0.0
    for item in items:
        total = item_total_sales(item)
        grand += total
        recomputed.append(item.model_copy(update={"total_sales": total}))
    return recomputed, round(grand, 2)


def calc_balance(
    total_sales: float,
    cash: float,
    checks: float,
    credit: float,
    expenses: float,
) -> float:
    """Balance = Total Sales − Cash − Checks − Credit − Expenses."""
    return round(
        float(total_sales)
        - float(cash)
        - float(checks)
        - float(credit)
        - float(expenses),
        2,
    )


def denom_total_from(body_denoms: CashDenominationCreate) -> float:
    return calc_denom_total(
        body_denoms.bill_1000,
        body_denoms.bill_500,
        body_denoms.bill_200,
        body_denoms.bill_100,
        body_denoms.bill_50,
        body_denoms.bill_20,
        body_denoms.coins,
    )


def validate_submitted_rows(items: List[DailyReportItemCreate]) -> None:
    """Mirror frontend completeness rules for submitted reports."""
    errors: List[str] = []
    for i, item in enumerate(items, start=1):
        label = f'{item.product_name}' + (f' ({item.weight})' if item.weight else '')
        if item.load_in is None or str(item.load_in).strip() == '':
            errors.append(f'Row {i} "{label}": Load-in required')
        if item.load_out_bundle is None or str(item.load_out_bundle).strip() == '':
            errors.append(f'Row {i} "{label}": Load-out/Bdl required')
        if item.load_out_piece is None:
            errors.append(f'Row {i} "{label}": Load-out/Pc required')
        if item.sales_bundle is None:
            errors.append(f'Row {i} "{label}": Sales/Bdl required')
        if item.sales_piece is None:
            errors.append(f'Row {i} "{label}": Sales/Pc required')
        if item.sales_peso_bundle is None:
            errors.append(f'Row {i} "{label}": ₱/Bdl required')
        if item.sales_peso_piece is None:
            errors.append(f'Row {i} "{label}": ₱/Pc required')
    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Incomplete daily report — fill all required row fields before submitting.",
                "errors": errors[:20],
                "error_count": len(errors),
            },
        )


def apply_poka_yoke(body: DailyReportCreate) -> Tuple[DailyReportCreate, float, float]:
    """
    Returns (normalized_body, total_sales, denom_total).
    Mutates totals / balance / cash to server-authoritative values.
    """
    items, total_sales = recompute_items(body.items)
    denom_total = denom_total_from(body.denominations)

    if body.status == "submitted":
        validate_submitted_rows(items)
        # Cash collection must equal counted denominations (Poka-Yoke)
        if abs(float(body.cash_collection) - denom_total) > TOLERANCE:
            # Auto-correct from bill/coin count — source of truth for cash
            cash = denom_total
        else:
            cash = round(float(body.cash_collection), 2)
    else:
        cash = round(float(body.cash_collection), 2)

    checks = round(float(body.checks_collection), 2)
    credit = round(float(body.credit_sales), 2)
    expenses = round(float(body.expenses), 2)
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
