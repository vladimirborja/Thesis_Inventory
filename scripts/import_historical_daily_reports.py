"""
Import Duque Jan–Jul 2026 Excel daily sheets as historical daily_transactions.

Treats rows as read-only history for viewing. Does NOT wipe existing data unless
--replace is passed (replaces only reports tagged as this historical import).

Usage (from project root):
    .venv/bin/python scripts/import_historical_daily_reports.py
    .venv/bin/python scripts/import_historical_daily_reports.py --replace
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.models import (
    Base,
    CashDenomination,
    DailyTransaction,
    DailyTransactionItem,
    User,
)
from api.services.daily_report_template import get_report_line_template

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XLSX = ROOT / "data" / "Duque_Daily_Transaction_Reports_Jan-Jul_2026.xlsx"
HIST_TAG = "historical-import:jan-jul-2026"
CATEGORY_HEADERS = {
    "TOCINO",
    "LONGANISA",
    "EMBOTIDO",
    "HAMBURGER PATTIES",
    "HAM",
    "SAUSAGES",
}


def parse_sheet_date(name: str) -> Optional[Tuple[date, int]]:
    """'1-3-26' -> (2026-01-03, 1); '3-17-26_2' -> (2026-03-17, 2)."""
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{2})(?:_(\d+))?", name.strip())
    if not m:
        return None
    month, day, yy, run = m.groups()
    year = 2000 + int(yy)
    return date(year, int(month), int(day)), int(run or 1)


def cell_num(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cell_str(v: Any) -> Optional[str]:
    if v is None or v == "":
        return None
    return str(v).strip()


def parse_prepared_by(raw: Any) -> Optional[str]:
    s = cell_str(raw) or ""
    if not s.lower().startswith("prepared by"):
        return None
    part = s.split(":", 1)
    name = part[1].strip() if len(part) > 1 else ""
    return name or None


def parse_sheet(ws) -> Dict[str, Any]:
    title_date = cell_str(ws.cell(2, 1).value) or ""
    prepared = parse_prepared_by(ws.cell(2, 6).value)

    template = get_report_line_template()
    by_key = {
        (r["product_name"].strip().lower(), (r["weight"] or "").strip().lower()): dict(r)
        for r in template
    }
    # Also allow Embo → Emba aliases from older template spellings
    aliases = {
        "embo x6 (m)": "emba x6 (m)",
        "embo x5 (l)": "emba x5 (l)",
        "embo single": "emba single",
    }

    items: List[Dict[str, Any]] = []
    current_cat = "UNCATEGORIZED"

    for r in range(4, 40):
        a = cell_str(ws.cell(r, 1).value)
        if not a:
            continue
        if a.upper() == "TOTAL SALES":
            break
        # Category header: all-caps or known title-case headers with no weight/qty
        upper = a.upper()
        weight = cell_str(ws.cell(r, 2).value)
        load_in = cell_str(ws.cell(r, 3).value)
        if upper in CATEGORY_HEADERS or (
            a.isupper() and weight is None and load_in is None and a != "TOTAL SALES"
        ):
            current_cat = "Hamburger Patties" if upper == "HAMBURGER PATTIES" else a
            continue

        name = a
        key_name = aliases.get(name.lower(), name.lower())
        key = (key_name, (weight or "").strip().lower())
        base = by_key.get(key)
        if base is None:
            # Fallback: match by product name only
            for (n, _w), row in by_key.items():
                if n == key_name:
                    base = dict(row)
                    break
        if base is None:
            base = {
                "category": current_cat,
                "product_name": name,
                "weight": weight,
                "sort_order": len(items),
            }
        else:
            base = dict(base)
            base["category"] = base.get("category") or current_cat

        sales_bundle = cell_num(ws.cell(r, 6).value)
        sales_piece = cell_num(ws.cell(r, 7).value)
        peso_b = cell_num(ws.cell(r, 8).value)
        peso_p = cell_num(ws.cell(r, 9).value)
        total = cell_num(ws.cell(r, 10).value) or 0.0
        price_b = cell_num(ws.cell(r, 11).value)
        price_p = cell_num(ws.cell(r, 12).value)

        # Excel often fills Total Sales only — park it in peso/bundle so UI totals match
        if (peso_b is None or peso_b == 0) and (peso_p is None or peso_p == 0) and total:
            if sales_bundle and price_b:
                peso_b = round(sales_bundle * price_b, 2)
                leftover = round(total - peso_b, 2)
                if leftover > 0:
                    peso_p = leftover
                elif leftover < 0:
                    peso_b = total
            elif sales_piece and price_p:
                peso_p = round(sales_piece * price_p, 2)
            else:
                peso_b = total

        row_total = round((peso_b or 0) + (peso_p or 0), 2)
        if row_total == 0 and total:
            row_total = total
            peso_b = total

        items.append(
            {
                "category": base["category"],
                "product_name": base["product_name"],
                "weight": base.get("weight") or weight,
                "load_in": load_in,
                "load_out_bundle": cell_str(ws.cell(r, 4).value),
                "load_out_piece": cell_num(ws.cell(r, 5).value),
                "sales_bundle": sales_bundle,
                "sales_piece": sales_piece,
                "sales_peso_bundle": peso_b,
                "sales_peso_piece": peso_p,
                "total_sales": row_total,
                "sort_order": base.get("sort_order", len(items)),
                "_price_bundle": price_b or base.get("price_bundle"),
                "_price_piece": price_p or base.get("price_piece"),
            }
        )

    # Footer reconciliation (labels in col G, values in col J)
    cash = checks = credit = expenses = balance = 0.0
    for r in range(23, 35):
        label = (cell_str(ws.cell(r, 7).value) or "").lower()
        val = cell_num(ws.cell(r, 10).value) or 0.0
        if "collection (cash)" in label or label.startswith("less:"):
            cash = val
        elif "checks" in label:
            checks = val
        elif "credit" in label:
            credit = val
        elif "expense" in label:
            expenses = val
        elif "balance" in label:
            balance = val

    # Prefer sheet TOTAL SALES cell if present
    sheet_total = cell_num(ws.cell(23, 10).value)
    items_total = round(sum(float(i["total_sales"] or 0) for i in items), 2)
    total_sales = sheet_total if sheet_total is not None else items_total
    if abs(items_total - total_sales) > 0.05 and sheet_total is not None:
        # Keep Excel header total authoritative for history display
        total_sales = sheet_total

    computed_balance = round(total_sales - cash - checks - credit - expenses, 2)
    # Prefer computed balance for system consistency; Excel Balance often = Total Sales
    if balance == total_sales and (cash or expenses):
        balance = computed_balance
    elif balance == 0:
        balance = computed_balance

    return {
        "prepared_by": prepared,
        "title": title_date,
        "items": items,
        "total_sales": total_sales,
        "cash_collection": cash,
        "checks_collection": checks,
        "credit_sales": credit,
        "expenses": expenses,
        "balance": balance,
    }


def pick_users(db: Session) -> Tuple[User, User]:
    primary = (
        db.query(User)
        .filter(User.can_input_transactions == True)  # noqa: E712
        .order_by(User.id.asc())
        .first()
    )
    if not primary:
        primary = db.query(User).order_by(User.id.asc()).first()
    if not primary:
        raise SystemExit("No users found — run scripts/seed.py first.")

    secondary = (
        db.query(User)
        .filter(User.id != primary.id, User.role.in_(("admin", "super_admin", "employee")))
        .order_by(User.id.asc())
        .first()
    ) or primary
    return primary, secondary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Jan–Jul 2026 historical daily reports")
    parser.add_argument("--file", type=Path, default=DEFAULT_XLSX)
    parser.add_argument(
        "--replace",
        action="store_true",
        help=f"Delete existing reports whose notes contain '{HIST_TAG}' before import",
    )
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"Excel not found: {args.file}")

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise SystemExit("DATABASE_URL missing — check .env")

    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)

    wb = load_workbook(args.file, data_only=True)
    sheets = [n for n in wb.sheetnames if n not in ("Index", "Price List")]

    with Session(engine) as db:
        primary, secondary = pick_users(db)
        print(f"Primary importer: {primary.name} (id={primary.id})")
        print(f"Duplicate-day importer: {secondary.name} (id={secondary.id})")

        if args.replace:
            doomed = (
                db.query(DailyTransaction)
                .filter(DailyTransaction.notes.contains(HIST_TAG))
                .all()
            )
            print(f"Replacing {len(doomed)} previously imported historical reports…")
            for tx in doomed:
                db.delete(tx)
            db.commit()

        created = skipped = 0
        for name in sheets:
            parsed_date = parse_sheet_date(name)
            if not parsed_date:
                print(f"  skip (bad name): {name}")
                skipped += 1
                continue
            report_date, run = parsed_date
            owner = primary if run == 1 else secondary
            existing = (
                db.query(DailyTransaction)
                .filter(
                    DailyTransaction.user_id == owner.id,
                    DailyTransaction.report_date == report_date,
                )
                .first()
            )
            if existing and HIST_TAG not in (existing.notes or ""):
                print(f"  skip (manual report exists): {name} → {report_date}")
                skipped += 1
                continue
            if existing:
                db.delete(existing)
                db.flush()

            data = parse_sheet(wb[name])
            notes_parts = [HIST_TAG, f"sheet:{name}"]
            if data["prepared_by"]:
                notes_parts.append(f"prepared_by:{data['prepared_by']}")
            if run > 1:
                notes_parts.append(f"run:{run}")

            tx = DailyTransaction(
                user_id=owner.id,
                report_date=report_date,
                client_name=None,
                total_sales=data["total_sales"],
                cash_collection=data["cash_collection"],
                checks_collection=data["checks_collection"],
                credit_sales=data["credit_sales"],
                expenses=data["expenses"],
                balance=data["balance"],
                status="submitted",
                notes="; ".join(notes_parts),
            )
            db.add(tx)
            db.flush()

            for item in data["items"]:
                payload = {k: v for k, v in item.items() if not k.startswith("_")}
                db.add(DailyTransactionItem(transaction_id=tx.id, **payload))

            db.add(
                CashDenomination(
                    transaction_id=tx.id,
                    bill_1000=0,
                    bill_500=0,
                    bill_200=0,
                    bill_100=0,
                    bill_50=0,
                    bill_20=0,
                    coins=0,
                    total_amount=0,
                )
            )
            created += 1

        db.commit()
        print(f"Done. imported={created} skipped={skipped} at {datetime.now().isoformat(timespec='seconds')}")
        print("Historical data is tagged for later wipe — tell me when to clear before Oct–Dec live use.")


if __name__ == "__main__":
    main()
