"""
Seed script — run once after creating the schema to populate demo data.

Usage:
    cp .env.example .env          # fill in DATABASE_URL
    pip install -r requirements.txt
    python scripts/seed.py
"""

import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import bcrypt

from api.models import (
    Base, User, Category, Warehouse, Supplier,
    Product, Ingredient,
)

DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(DATABASE_URL)

print("Creating tables...")
Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    # ── Check if already seeded ──────────────────────────────────────────────
    if db.query(User).count() > 0:
        print("Database already seeded. Skipping.")
        sys.exit(0)

    # ── Users ────────────────────────────────────────────────────────────────
    # Default password for ALL demo accounts: admin123
    DEFAULT_PASSWORD = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
    COMPANY = "Duque Food Products"

    users = [
        User(name="Jesus F. Duque Jr.", email="superadmin@duquefood.com", password=DEFAULT_PASSWORD,
             role="super_admin", company_name=COMPANY),
        User(name="Plant Admin", email="admin@duquefood.com", password=DEFAULT_PASSWORD,
             role="admin", company_name=COMPANY),
        User(name="Floor Operator", email="employee@duquefood.com", password=DEFAULT_PASSWORD,
             role="employee", company_name=COMPANY, can_input_transactions=True),
    ]
    db.add_all(users)
    db.flush()

    # ── Categories ───────────────────────────────────────────────────────────
    cats = [
        Category(name="Processed Meats", slug="processed-meats"),
        Category(name="Raw Ingredients", slug="raw-ingredients"),
        Category(name="Packaging Materials", slug="packaging-materials"),
    ]
    db.add_all(cats)
    db.flush()
    cat_map = {c.slug: c.id for c in cats}

    # ── Warehouses ───────────────────────────────────────────────────────────
    warehouses = [
        Warehouse(name="Cold Storage", location="Purok 7, Malino — Temperature Controlled"),
        Warehouse(name="Production Staging", location="Main Plant Floor"),
        Warehouse(name="Packaging Area", location="Packing Line 1"),
    ]
    db.add_all(warehouses)
    db.flush()

    # ── Suppliers ────────────────────────────────────────────────────────────
    suppliers = [
        Supplier(
            name="Central Luzon Meat Supply",
            contact_name="Maria Santos",
            email="orders@clmeats.ph",
            phone="+63 917 000 0001",
            address="San Fernando, Pampanga",
            lead_time_days=5,
        ),
        Supplier(
            name="Pampanga Spice & Seasoning Co.",
            contact_name="Juan Reyes",
            email="sales@pampangaspice.ph",
            phone="+63 917 000 0002",
            address="City of San Fernando, Pampanga",
            lead_time_days=7,
        ),
        Supplier(
            name="Metro Packaging Solutions",
            contact_name="Ana Cruz",
            email="hello@metropack.ph",
            phone="+63 917 000 0003",
            address="Valenzuela City",
            lead_time_days=10,
        ),
    ]
    db.add_all(suppliers)
    db.flush()

    # ── Products — Excel Price List only (no invented stock/cost) ────────────
    from api.services.product_catalog import catalog_as_dicts

    meats_id = cat_map["processed-meats"]
    products = [Product(**row) for row in catalog_as_dicts(category_id=meats_id)]
    db.add_all(products)
    db.flush()

    # ── Ingredients (structure only — quantities start at 0 until counted) ───
    ingredients = [
        Ingredient(name="Ground Pork", quantity=0.0, unit="kg", min_stock_level=0.0, lead_time_days=3),
        Ingredient(name="Ground Beef", quantity=0.0, unit="kg", min_stock_level=0.0, lead_time_days=3),
        Ingredient(name="Curing Salt", quantity=0.0, unit="kg", min_stock_level=0.0, lead_time_days=10),
        Ingredient(name="Brown Sugar", quantity=0.0, unit="kg", min_stock_level=0.0, lead_time_days=7),
        Ingredient(name="Garlic", quantity=0.0, unit="kg", min_stock_level=0.0, lead_time_days=4),
        Ingredient(name="Black Pepper", quantity=0.0, unit="kg", min_stock_level=0.0, lead_time_days=7),
        Ingredient(name="Food Casing / Wrapper", quantity=0.0, unit="pcs", min_stock_level=0.0, lead_time_days=10),
    ]
    db.add_all(ingredients)
    db.commit()

print("✅ Seed complete (Excel catalog, zero stock — no demo money/qty).")
print("   Default password: admin123")
print("   superadmin@duquefood.com / admin@duquefood.com / employee@duquefood.com")
print("   Next: python scripts/import_historical_daily_reports.py")
