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
from passlib.context import CryptContext

from api.models import (
    Base, User, Category, Warehouse, Supplier,
    Product, Ingredient, StockTransaction
)

DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(DATABASE_URL)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("Creating tables...")
Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    # ── Check if already seeded ──────────────────────────────────────────────
    if db.query(User).count() > 0:
        print("Database already seeded. Skipping.")
        sys.exit(0)

    # ── Users ────────────────────────────────────────────────────────────────
    # Default password for ALL demo accounts: admin123
    DEFAULT_PASSWORD = pwd_context.hash("admin123")
    COMPANY = "Duque Food Products"

    users = [
        User(name="Jesus F. Duque Jr.", email="superadmin@duquefood.com", password=DEFAULT_PASSWORD,
             role="super_admin", company_name=COMPANY),
        User(name="Plant Admin", email="admin@duquefood.com", password=DEFAULT_PASSWORD,
             role="admin", company_name=COMPANY),
        User(name="Floor Operator", email="employee@duquefood.com", password=DEFAULT_PASSWORD,
             role="employee", company_name=COMPANY),
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

    # ── Products (Duque Food Products catalog) — prices in PHP ───────────────
    meats_id = cat_map["processed-meats"]
    products = [
        Product(
            name="Skinless Longganisa", sku="DFP-LONG-001", barcode="4809001001001",
            category_id=meats_id,
            description="Skinless Filipino longganisa — savory-sweet, ready for retail and foodservice.",
            cost_price=180.00, selling_price=250.00,
            min_stock_level=40, quantity=120, unit_of_measure="kg",
            lead_time_days=5,
        ),
        Product(
            name="Tocino", sku="DFP-TOCI-002", barcode="4809001001002",
            category_id=meats_id,
            description="Sweet cured tocino slices for home and institutional buyers.",
            cost_price=200.00, selling_price=280.00,
            min_stock_level=35, quantity=95, unit_of_measure="kg",
            lead_time_days=5,
        ),
        Product(
            name="Ham", sku="DFP-HAM-003", barcode="4809001001003",
            category_id=meats_id,
            description="Processed ham — sliced or whole for local customers and businesses.",
            cost_price=320.00, selling_price=450.00,
            min_stock_level=20, quantity=48, unit_of_measure="kg",
            lead_time_days=7,
        ),
        Product(
            name="Embotido", sku="DFP-EMBO-004", barcode="4809001001004",
            category_id=meats_id,
            description="Classic Filipino embotido loaf for celebrations and everyday meals.",
            cost_price=160.00, selling_price=230.00,
            min_stock_level=30, quantity=70, unit_of_measure="kg",
            lead_time_days=5,
        ),
        Product(
            name="Bologna", sku="DFP-BOLO-005", barcode="4809001001005",
            category_id=meats_id,
            description="Smooth bologna for sandwiches, trays, and bulk foodservice orders.",
            cost_price=140.00, selling_price=200.00,
            min_stock_level=25, quantity=60, unit_of_measure="kg",
            lead_time_days=7,
        ),
        Product(
            name="Patties", sku="DFP-PATT-006", barcode="4809001001006",
            category_id=meats_id,
            description="Ready-to-cook meat patties for canteens, stalls, and households.",
            cost_price=150.00, selling_price=220.00,
            min_stock_level=50, quantity=18, unit_of_measure="packs",
            lead_time_days=4,
        ),
        Product(
            name="Siomai", sku="DFP-SIOM-007", barcode="4809001001007",
            category_id=meats_id,
            description="Pork siomai — steamed or fried; packed for retail and food carts.",
            cost_price=120.00, selling_price=180.00,
            min_stock_level=60, quantity=150, unit_of_measure="packs",
            lead_time_days=3,
        ),
    ]
    db.add_all(products)
    db.flush()

    # ── Ingredients (meat processing) ────────────────────────────────────────
    ingredients = [
        Ingredient(name="Ground Pork", quantity=200.0, unit="kg", min_stock_level=50.0, lead_time_days=3),
        Ingredient(name="Ground Beef", quantity=80.0, unit="kg", min_stock_level=25.0, lead_time_days=3),
        Ingredient(name="Curing Salt", quantity=15.0, unit="kg", min_stock_level=5.0, lead_time_days=10),
        Ingredient(name="Brown Sugar", quantity=40.0, unit="kg", min_stock_level=15.0, lead_time_days=7),
        Ingredient(name="Garlic", quantity=25.0, unit="kg", min_stock_level=8.0, lead_time_days=4),
        Ingredient(name="Black Pepper", quantity=8.0, unit="kg", min_stock_level=3.0, lead_time_days=7),
        Ingredient(name="Food Casing / Wrapper", quantity=500.0, unit="pcs", min_stock_level=100.0, lead_time_days=10),
    ]
    db.add_all(ingredients)
    db.flush()

    # ── Demo Transactions ─────────────────────────────────────────────────────
    admin_id = users[1].id
    emp_id = users[2].id
    wh_ids = [w.id for w in warehouses]

    txs = [
        StockTransaction(
            product_id=products[0].id, warehouse_id=wh_ids[0], supplier_id=suppliers[0].id,
            user_id=admin_id, type="stock-in", quantity=50,
            reference_number="PO-2026-DFP-001", notes="Cold storage receipt — Skinless Longganisa"),
        StockTransaction(
            product_id=products[5].id, warehouse_id=wh_ids[1],
            user_id=emp_id, type="stock-out", quantity=12,
            reference_number="SO-2026-018", notes="Released Patties for weekend orders"),
        StockTransaction(
            product_id=products[1].id, warehouse_id=wh_ids[0],
            user_id=admin_id, type="adjustment", quantity=-3,
            reference_number="ADJ-DFP-002", notes="Tocino quality hold / sample pull"),
    ]
    db.add_all(txs)
    db.commit()

print("✅ Seed complete. Default password for all accounts: admin123")
print("   superadmin@duquefood.com / admin@duquefood.com / employee@duquefood.com")
