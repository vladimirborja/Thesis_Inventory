"""
api/routers/daily_reports.py — Employee daily transaction reports + aggregated views.
"""

from datetime import date
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session, joinedload

from api.database import get_db
from api.dependencies import get_current_user, require_admin, require_transaction_input, log_activity
from api.models import (
    DailyTransaction, DailyTransactionItem, CashDenomination, User,
)
from api.schemas import (
    DailyReportCreate,
    DailyReportResponse,
    DailyReportItemResponse,
    CashDenominationResponse,
    DailyReportAggregateRow,
)
from api.services.daily_report_template import get_report_line_template, calc_denom_total

router = APIRouter()


def _enrich_report(tx: DailyTransaction) -> DailyReportResponse:
    data = DailyReportResponse.model_validate(tx)
    data.user_name = tx.user.name if tx.user else None
    data.items = [DailyReportItemResponse.model_validate(i) for i in tx.items]
    if tx.denominations:
        data.denominations = CashDenominationResponse.model_validate(tx.denominations)
    return data


def _load_report(db: Session, report_id: int) -> DailyTransaction:
    tx = (
        db.query(DailyTransaction)
        .options(
            joinedload(DailyTransaction.items),
            joinedload(DailyTransaction.denominations),
            joinedload(DailyTransaction.user),
        )
        .filter(DailyTransaction.id == report_id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return tx


def _can_access(user: User, tx: DailyTransaction) -> bool:
    return user.role in ("admin", "super_admin") or tx.user_id == user.id


@router.get("/template")
def report_template(_: User = Depends(get_current_user)):
    """Blank line-item rows matching the Duque daily transaction Excel."""
    return get_report_line_template()


@router.get("", response_model=List[DailyReportResponse])
def list_reports(
    report_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(DailyTransaction)
        .options(
            joinedload(DailyTransaction.items),
            joinedload(DailyTransaction.denominations),
            joinedload(DailyTransaction.user),
        )
        .order_by(DailyTransaction.report_date.desc())
    )
    if current_user.role not in ("admin", "super_admin"):
        q = q.filter(DailyTransaction.user_id == current_user.id)
    if report_date:
        q = q.filter(DailyTransaction.report_date == report_date)
    if status:
        q = q.filter(DailyTransaction.status == status)
    return [_enrich_report(tx) for tx in q.all()]


@router.get("/aggregate", response_model=List[DailyReportAggregateRow])
def aggregate_reports(
    group_by: Literal["week", "month", "year"] = Query("month"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    q = db.query(DailyTransaction).filter(DailyTransaction.status == "submitted")
    if date_from:
        q = q.filter(DailyTransaction.report_date >= date_from)
    if date_to:
        q = q.filter(DailyTransaction.report_date <= date_to)
    reports = q.all()

    buckets: dict = {}
    for tx in reports:
        if group_by == "week":
            iso = tx.report_date.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
            label = key
        elif group_by == "month":
            key = f"{tx.report_date.year:04d}-{tx.report_date.month:02d}"
            months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
            label = f"{months[tx.report_date.month - 1]} {tx.report_date.year}"
        else:
            key = str(tx.report_date.year)
            label = key

        if key not in buckets:
            buckets[key] = {
                "period_key": key,
                "label": label,
                "report_count": 0,
                "total_sales": 0.0,
                "cash_collection": 0.0,
                "expenses": 0.0,
                "balance": 0.0,
            }
        b = buckets[key]
        b["report_count"] += 1
        b["total_sales"] += float(tx.total_sales)
        b["cash_collection"] += float(tx.cash_collection)
        b["expenses"] += float(tx.expenses)
        b["balance"] += float(tx.balance)

    rows = sorted(buckets.values(), key=lambda x: x["period_key"])
    return [DailyReportAggregateRow(**{k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()}) for r in rows]


@router.get("/by-date/{report_date}", response_model=DailyReportResponse)
def get_report_by_date(
    report_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = (
        db.query(DailyTransaction)
        .options(
            joinedload(DailyTransaction.items),
            joinedload(DailyTransaction.denominations),
            joinedload(DailyTransaction.user),
        )
        .filter(
            DailyTransaction.user_id == current_user.id,
            DailyTransaction.report_date == report_date
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="No report found for this date")
    return _enrich_report(tx)


@router.get("/{report_id}", response_model=DailyReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = _load_report(db, report_id)
    if not _can_access(current_user, tx):
        raise HTTPException(status_code=403, detail="Access denied")
    return _enrich_report(tx)


@router.post("", response_model=DailyReportResponse, status_code=201)
def create_report(
    body: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transaction_input),
):
    existing = (
        db.query(DailyTransaction)
        .filter(
            DailyTransaction.user_id == current_user.id,
            DailyTransaction.report_date == body.report_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Report already exists for {body.report_date}. Use PUT to update.",
        )

    total_sales = round(sum(float(i.total_sales) for i in body.items), 2)
    denom_total = calc_denom_total(
        body.denominations.bill_1000,
        body.denominations.bill_500,
        body.denominations.bill_200,
        body.denominations.bill_100,
        body.denominations.bill_50,
        body.denominations.bill_20,
        body.denominations.coins,
    )

    tx = DailyTransaction(
        user_id=current_user.id,
        report_date=body.report_date,
        client_name=body.client_name,
        total_sales=total_sales,
        cash_collection=body.cash_collection,
        checks_collection=body.checks_collection,
        credit_sales=body.credit_sales,
        expenses=body.expenses,
        balance=body.balance,
        status=body.status,
        notes=body.notes,
    )
    db.add(tx)
    db.flush()

    for item in body.items:
        db.add(DailyTransactionItem(transaction_id=tx.id, **item.model_dump()))

    db.add(CashDenomination(
        transaction_id=tx.id,
        **body.denominations.model_dump(),
        total_amount=denom_total,
    ))

    log_activity(db, current_user.id, "daily-report-create", {
        "report_id": tx.id,
        "report_date": str(body.report_date),
        "total_sales": total_sales,
        "denom_total": denom_total,
    })
    db.commit()
    db.refresh(tx)
    return _enrich_report(_load_report(db, tx.id))


@router.put("/{report_id}", response_model=DailyReportResponse)
def update_report(
    report_id: int,
    body: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transaction_input),
):
    tx = _load_report(db, report_id)
    if not _can_access(current_user, tx):
        raise HTTPException(status_code=403, detail="Access denied")
    if tx.status == "submitted" and current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=400, detail="Submitted reports cannot be edited")

    total_sales = round(sum(float(i.total_sales) for i in body.items), 2)
    denom_total = calc_denom_total(
        body.denominations.bill_1000,
        body.denominations.bill_500,
        body.denominations.bill_200,
        body.denominations.bill_100,
        body.denominations.bill_50,
        body.denominations.bill_20,
        body.denominations.coins,
    )

    tx.report_date = body.report_date
    tx.client_name = body.client_name
    tx.total_sales = total_sales
    tx.cash_collection = body.cash_collection
    tx.checks_collection = body.checks_collection
    tx.credit_sales = body.credit_sales
    tx.expenses = body.expenses
    tx.balance = body.balance
    tx.status = body.status
    tx.notes = body.notes

    db.query(DailyTransactionItem).filter(DailyTransactionItem.transaction_id == tx.id).delete()
    for item in body.items:
        db.add(DailyTransactionItem(transaction_id=tx.id, **item.model_dump()))

    if tx.denominations:
        for k, v in body.denominations.model_dump().items():
            setattr(tx.denominations, k, v)
        tx.denominations.total_amount = denom_total
    else:
        db.add(CashDenomination(transaction_id=tx.id, **body.denominations.model_dump(), total_amount=denom_total))

    log_activity(db, current_user.id, "daily-report-update", {"report_id": tx.id})
    db.commit()
    return _enrich_report(_load_report(db, tx.id))


@router.post("/upsert", response_model=DailyReportResponse, status_code=200)
def upsert_report(
    body: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transaction_input),
):
    """
    Create a new daily report, or fully replace an existing one for the same
    (user_id, report_date) pair.  The frontend never needs to track report IDs.
    """
    total_sales = round(sum(float(i.total_sales) for i in body.items), 2)
    denom_total = calc_denom_total(
        body.denominations.bill_1000,
        body.denominations.bill_500,
        body.denominations.bill_200,
        body.denominations.bill_100,
        body.denominations.bill_50,
        body.denominations.bill_20,
        body.denominations.coins,
    )

    existing = (
        db.query(DailyTransaction)
        .filter(
            DailyTransaction.user_id == current_user.id,
            DailyTransaction.report_date == body.report_date,
        )
        .first()
    )

    if existing:
        # ── UPDATE path ──────────────────────────────────────────────────────
        # Admins can always overwrite; employees can only overwrite their own drafts
        if existing.status == "submitted" and current_user.role not in ("admin", "super_admin"):
            raise HTTPException(
                status_code=400,
                detail="A submitted report already exists for this date. Ask an admin to unlock it.",
            )
        tx = existing
        tx.report_date      = body.report_date
        tx.client_name      = body.client_name
        tx.total_sales      = total_sales
        tx.cash_collection  = body.cash_collection
        tx.checks_collection = body.checks_collection
        tx.credit_sales     = body.credit_sales
        tx.expenses         = body.expenses
        tx.balance          = body.balance
        tx.status           = body.status
        tx.notes            = body.notes

        db.query(DailyTransactionItem).filter(
            DailyTransactionItem.transaction_id == tx.id
        ).delete()
        for item in body.items:
            db.add(DailyTransactionItem(transaction_id=tx.id, **item.model_dump()))

        if tx.denominations:
            for k, v in body.denominations.model_dump().items():
                setattr(tx.denominations, k, v)
            tx.denominations.total_amount = denom_total
        else:
            db.add(CashDenomination(
                transaction_id=tx.id,
                **body.denominations.model_dump(),
                total_amount=denom_total,
            ))

        log_activity(db, current_user.id, "daily-report-update", {
            "report_id": tx.id,
            "report_date": str(body.report_date),
            "total_sales": total_sales,
        })
    else:
        # ── CREATE path ──────────────────────────────────────────────────────
        tx = DailyTransaction(
            user_id=current_user.id,
            report_date=body.report_date,
            client_name=body.client_name,
            total_sales=total_sales,
            cash_collection=body.cash_collection,
            checks_collection=body.checks_collection,
            credit_sales=body.credit_sales,
            expenses=body.expenses,
            balance=body.balance,
            status=body.status,
            notes=body.notes,
        )
        db.add(tx)
        db.flush()

        for item in body.items:
            db.add(DailyTransactionItem(transaction_id=tx.id, **item.model_dump()))

        db.add(CashDenomination(
            transaction_id=tx.id,
            **body.denominations.model_dump(),
            total_amount=denom_total,
        ))

        log_activity(db, current_user.id, "daily-report-create", {
            "report_id": tx.id,
            "report_date": str(body.report_date),
            "total_sales": total_sales,
            "denom_total": denom_total,
        })

    db.commit()
    return _enrich_report(_load_report(db, tx.id))

