"""
Replace inventory products with the real Excel catalog (Jan–Jul 2026).

- Adds weight / piece_price columns if missing
- Removes demo/fake SKUs and demo stock vouchers
- Upserts products from api.services.product_catalog (Excel prices only)

Usage:
    .venv/bin/python scripts/sync_products_from_excel.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from api.models import Base, Category, Product, StockTransaction
from api.services.product_catalog import catalog_as_dicts

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL missing")


def ensure_columns(engine) -> None:
    statements = [
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS weight VARCHAR(50)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS piece_price NUMERIC(12, 2) NOT NULL DEFAULT 0",
    ]
    with engine.begin() as conn:
        for sql in statements:
            conn.execute(text(sql))


def main() -> None:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    ensure_columns(engine)

    with Session(engine) as db:
        meats = (
            db.query(Category)
            .filter(Category.slug == "processed-meats")
            .first()
        )
        if not meats:
            meats = Category(name="Processed Meats", slug="processed-meats")
            db.add(meats)
            db.flush()

        catalog = catalog_as_dicts(category_id=meats.id)
        keep_skus = {row["sku"] for row in catalog}

        # Drop demo stock vouchers so we can safely replace fake SKUs
        demo_refs = ("PO-2026-DFP-001", "SO-2026-018", "ADJ-DFP-002")
        deleted_tx = (
            db.query(StockTransaction)
            .filter(StockTransaction.reference_number.in_(demo_refs))
            .delete(synchronize_session=False)
        )
        print(f"Removed {deleted_tx} demo stock voucher(s)")

        existing = {p.sku: p for p in db.query(Product).all()}

        # Delete SKUs not in Excel catalog (and with no remaining FKs)
        for sku, product in list(existing.items()):
            if sku in keep_skus:
                continue
            still_linked = (
                db.query(StockTransaction)
                .filter(StockTransaction.product_id == product.id)
                .count()
            )
            if still_linked:
                print(f"  keep linked legacy SKU {sku} (id={product.id}) — has {still_linked} tx")
                continue
            db.delete(product)
            print(f"  deleted fake/legacy SKU {sku}")
            existing.pop(sku, None)

        for row in catalog:
            sku = row["sku"]
            product = existing.get(sku)
            if product is None:
                product = Product(**row)
                db.add(product)
                print(f"  + {row['name']}  bundle=₱{row['selling_price']}  piece=₱{row['piece_price']}")
            else:
                product.name = row["name"]
                product.weight = row["weight"]
                product.selling_price = row["selling_price"]
                product.piece_price = row["piece_price"]
                product.cost_price = 0
                product.description = row["description"]
                product.category_id = meats.id
                product.unit_of_measure = "bundles"
                # Do not invent stock — leave quantity as-is only if already 0; zero fake demo qty
                if product.quantity and sku.startswith("DFP-") is False:
                    pass
                # Reset seeded demo quantities to 0
                product.quantity = 0
                product.min_stock_level = 0
                print(f"  ~ {row['name']}  bundle=₱{row['selling_price']}  piece=₱{row['piece_price']}")

        db.commit()
        total = db.query(Product).count()
        print(f"Done. products in catalog: {total}")


if __name__ == "__main__":
    main()
