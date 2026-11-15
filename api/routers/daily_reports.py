"""
api/routers/daily_reports.py — Employee daily transaction reports + compliance.
"""

from datetime import date, timedelta
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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
    ComplianceSummary,
    ComplianceDayStatus,
)
from api.services.daily_report_template import get_report_line_template
from api.services.daily_report_poka_yoke import apply_poka_yoke

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


def _iter_dates(date_from: date, date_to: date):
    cur = date_from
    while cur <= date_to:
        yield cur
        cur += timedelta(days=1)


def _persist_report_body(
    db: Session,
    tx: DailyTransaction,
    body: DailyReportCreate,
    total_sales: float,
    denom_total: float,
) -> None:
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


@router.get("/template")
def report_template(_: User = Depends(get_current_user)):
    """Blank line-item rows matching the Duque daily transaction Excel."""
    return get_report_line_template()


@router.get("/compliance", response_model=ComplianceSummary)
def compliance_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    DIMS compliance view: submitted / draft / missing days for the range.
    Employees see only themselves; admins can filter by user_id or see all inputters.
    """
    today = date.today()
    end = date_to or today
    start = date_from or (end - timedelta(days=29))
    if start > end:
        raise HTTPException(status_code=400, detail="date_from must be on or before date_to")

    is_admin = current_user.role in ("admin", "super_admin")

    # Target users expected to file daily reports (operators with input permission)
    if is_admin:
        q_users = db.query(User).filter(User.can_input_transactions == True)  # noqa: E712
        if user_id:
            q_users = q_users.filter(User.id == user_id)
        target_users = q_users.all()
    else:
        target_users = [current_user]

    if not target_users:
        return ComplianceSummary(
            date_from=start,
            date_to=end,
            expected_days=0,
            submitted_days=0,
            draft_days=0,
            missing_days=0,
            missing_rate_percent=0.0,
            submission_rate_percent=0.0,
            today_status="missing",
            days=[],
            missing_today=[],
        )

    target_ids = [u.id for u in target_users]
    user_map = {u.id: u for u in target_users}

    reports = (
        db.query(DailyTransaction)
        .filter(
            DailyTransaction.user_id.in_(target_ids),
            DailyTransaction.report_date >= start,
            DailyTransaction.report_date <= end,
        )
        .all()
    )

    # For employee self-view: one row per calendar day for that user
    # For admin overview without user_id: aggregate "any submitted" is less useful —
    # we build per-user-day for the selected user, or for current_user if employee.
    focus_user_id = user_id if (is_admin and user_id) else (current_user.id if not is_admin else None)

    by_user_date = {(r.user_id, r.report_date): r for r in reports}

    days: List[ComplianceDayStatus] = []
    submitted = draft = missing = 0

    if focus_user_id is not None:
        for d in _iter_dates(start, end):
            tx = by_user_date.get((focus_user_id, d))
            if tx is None:
                status = "missing"
                missing += 1
                days.append(ComplianceDayStatus(
                    date=d, status=status, user_id=focus_user_id,
                    user_name=user_map[focus_user_id].name if focus_user_id in user_map else None,
                ))
            else:
                status = tx.status if tx.status in ("submitted", "draft") else "draft"
                if status == "submitted":
                    submitted += 1
                else:
                    draft += 1
                days.append(ComplianceDayStatus(
                    date=d,
                    status=status,
                    report_id=tx.id,
                    user_id=tx.user_id,
                    user_name=user_map.get(tx.user_id).name if tx.user_id in user_map else None,
                    total_sales=float(tx.total_sales),
                    submitted_at=tx.updated_at if status == "submitted" else None,
                ))
        expected = (end - start).days + 1
    else:
        # Admin org-wide: expected = users × days; calendar days use worst status that day
        expected = len(target_ids) * ((end - start).days + 1)
        for d in _iter_dates(start, end):
            day_missing = day_draft = 0
            for uid in target_ids:
                tx = by_user_date.get((uid, d))
                if tx is None:
                    missing += 1
                    day_missing += 1
                elif tx.status == "submitted":
                    submitted += 1
                else:
                    draft += 1
                    day_draft += 1
            if day_missing:
                org_status = "missing"
            elif day_draft:
                org_status = "draft"
            else:
                org_status = "submitted"
            days.append(ComplianceDayStatus(date=d, status=org_status))

    missing_today: List[ComplianceDayStatus] = []
    today_status = "missing"
    if is_admin:
        for uid in target_ids:
            tx = by_user_date.get((uid, today))
            if tx is None or tx.status != "submitted":
                missing_today.append(ComplianceDayStatus(
                    date=today,
                    status="missing" if tx is None else tx.status,
                    report_id=tx.id if tx else None,
                    user_id=uid,
                    user_name=user_map[uid].name,
                    total_sales=float(tx.total_sales) if tx else None,
                ))
        # Org today_status: submitted if everyone filed
        today_status = "submitted" if not missing_today else "missing"
    else:
        tx = by_user_date.get((current_user.id, today))
        if tx is None:
            today_status = "missing"
        else:
            today_status = tx.status if tx.status in ("submitted", "draft") else "draft"

    expected = max(expected, 1)
    missing_rate = round(100.0 * missing / expected, 2)
    submission_rate = round(100.0 * submitted / expected, 2)

    return ComplianceSummary(
        date_from=start,
        date_to=end,
        expected_days=expected,
        submitted_days=submitted,
        draft_days=draft,
        missing_days=missing,
        missing_rate_percent=missing_rate,
        submission_rate_percent=submission_rate,
        today_status=today_status,
        days=days,
        missing_today=missing_today,
    )


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
    body, total_sales, denom_total = apply_poka_yoke(body)

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
        "balance": body.balance,
        "status": body.status,
    })
    db.commit()
    return _enrich_report(_load_report(db, tx.id))


@router.put("/{report_id}", response_model=DailyReportResponse)
def update_report(
    report_id: int,
    body: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transaction_input),
):
    body, total_sales, denom_total = apply_poka_yoke(body)

    tx = _load_report(db, report_id)
    if not _can_access(current_user, tx):
        raise HTTPException(status_code=403, detail="Access denied")
    if tx.status == "submitted" and current_user.role not in ("admin", "super_admin"):
        raise HTTPException(status_code=400, detail="Submitted reports cannot be edited")

    _persist_report_body(db, tx, body, total_sales, denom_total)

    log_activity(db, current_user.id, "daily-report-update", {
        "report_id": tx.id,
        "total_sales": total_sales,
        "balance": body.balance,
        "status": body.status,
    })
    db.commit()
    return _enrich_report(_load_report(db, tx.id))


@router.post("/upsert", response_model=DailyReportResponse, status_code=200)
def upsert_report(
    body: DailyReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_transaction_input),
):
    """
    Create or replace a daily report for (user_id, report_date).
    Totals and balance are server-computed (Poka-Yoke).
    """
    body, total_sales, denom_total = apply_poka_yoke(body)

    existing = (
        db.query(DailyTransaction)
        .filter(
            DailyTransaction.user_id == current_user.id,
            DailyTransaction.report_date == body.report_date,
        )
        .first()
    )

    if existing:
        if existing.status == "submitted" and current_user.role not in ("admin", "super_admin"):
            raise HTTPException(
                status_code=400,
                detail="A submitted report already exists for this date. Ask an admin to unlock it.",
            )
        tx = existing
        _persist_report_body(db, tx, body, total_sales, denom_total)
        log_activity(db, current_user.id, "daily-report-update", {
            "report_id": tx.id,
            "report_date": str(body.report_date),
            "total_sales": total_sales,
            "balance": body.balance,
            "status": body.status,
        })
    else:
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
            "balance": body.balance,
            "status": body.status,
        })

    db.commit()
    return _enrich_report(_load_report(db, tx.id))
