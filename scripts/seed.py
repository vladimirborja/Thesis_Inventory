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

    users = [
        User(name="John Doe",    email="superadmin@foodprocessing.com", password=DEFAULT_PASSWORD,
             role="super_admin", company_name="Apex Food Processing Corp"),
        User(name="Alice Smith", email="admin@foodprocessing.com",      password=DEFAULT_PASSWORD,
             role="admin",       company_name="Apex Food Processing Corp"),
        User(name="Bob Johnson", email="employee@foodprocessing.com",   password=DEFAULT_PASSWORD,
             role="employee",    company_name="Apex Food Processing Corp"),
    ]
    db.add_all(users)
    db.flush()

    # ── Categories ───────────────────────────────────────────────────────────
    cats = [
        Category(name="Raw Ingredients",        slug="raw-ingredients"),
        Category(name="Packaging Materials",    slug="packaging-materials"),
        Category(name="Finished Goods",         slug="finished-goods"),
        Category(name="Additives & Preservatives", slug="additives-preservatives"),
    ]
    db.add_all(cats)
    db.flush()
    cat_map = {c.slug: c.id for c in cats}

    # ── Warehouses ───────────────────────────────────────────────────────────
    warehouses = [
        Warehouse(name="Central Cold Storage",  location="Section A - Temperature Controlled"),
        Warehouse(name="Raw Materials Depot",   location="Warehouse 3, Bay B"),
        Warehouse(name="Packaging Storehouse",  location="Warehouse 1, Floor 2"),
        Warehouse(name="Finished Goods Yard",   location="Loading Bay 5"),
    ]
    db.add_all(warehouses)
    db.flush()

    # ── Suppliers ────────────────────────────────────────────────────────────
    suppliers = [
        Supplier(name="Agri-Grow Farms Inc.",   contact_name="Robert Vance",
                 email="vance@agrigrow.com",    phone="+63 905 123 4567",
                 address="Davao City, Philippines"),
        Supplier(name="PolyPack Plastics Ltd.", contact_name="Sarah Jenkins",
                 email="sjenkins@polypack.com", phone="+63 917 987 6543",
                 address="Valenzuela City, Philippines"),
        Supplier(name="Global Additives Co.",   contact_name="Dr. Ken Suzuki",
                 email="suzuki@globaladditives.com", phone="+81 3 5555 0192",
                 address="Tokyo, Japan"),
    ]
    db.add_all(suppliers)
    db.flush()

    # ── Products ─────────────────────────────────────────────────────────────
    products = [
        Product(name="Premium Semolina Wheat Flour", sku="RM-FLOUR-001",
                barcode="4801234567011", category_id=cat_map["raw-ingredients"],
                description="High gluten flour for pasta processing",
                cost_price=35.00, selling_price=50.00,
                min_stock_level=100, quantity=450, unit_of_measure="bags (25kg)"),
        Product(name="BPA-Free Vacuum Sealing Film",  sku="PK-FILM-002",
                barcode="4801234567028", category_id=cat_map["packaging-materials"],
                description="200mm barrier roll for meat packaging",
                cost_price=150.00, selling_price=220.00,
                min_stock_level=20, quantity=12, unit_of_measure="rolls (100m)"),
        Product(name="Canned Tomato Paste Concentrated", sku="RM-TPAS-003",
                barcode="4801234567035", category_id=cat_map["raw-ingredients"],
                description="Concentrated paste, Brix 28-30%",
                cost_price=85.00, selling_price=120.00,
                min_stock_level=50, quantity=3, unit_of_measure="drums (50kg)"),
        Product(name="Natural Cane Sugar Refined", sku="RM-SUGR-004",
                barcode="4801234567042", category_id=cat_map["raw-ingredients"],
                description="Pure cane sugar, fine grade",
                cost_price=45.00, selling_price=60.00,
                min_stock_level=200, quantity=180, unit_of_measure="bags (50kg)"),
        Product(name="Organic Citric Acid Powder", sku="AD-CITR-005",
                barcode="4801234567059", category_id=cat_map["additives-preservatives"],
                description="USP/FCC grade food acidulant",
                cost_price=95.00, selling_price=140.00,
                min_stock_level=30, quantity=45, unit_of_measure="bags (25kg)"),
        Product(name="Sweet Chilli Sauce (Finished)", sku="FG-CHLI-006",
                barcode="4801234567066", category_id=cat_map["finished-goods"],
                description="Bottled sweet chilli sauce ready for retail",
                cost_price=22.00, selling_price=38.00,
                min_stock_level=500, quantity=1250, unit_of_measure="cases (24x250ml)"),
    ]
    db.add_all(products)
    db.flush()

    # ── Ingredients ──────────────────────────────────────────────────────────
    ingredients = [
        Ingredient(name="Tomato Paste",     quantity=150.0, unit="kg",  min_stock_level=50.0),
        Ingredient(name="Cane Sugar",       quantity=300.0, unit="kg",  min_stock_level=100.0),
        Ingredient(name="Chilli Pepper",    quantity=80.0,  unit="kg",  min_stock_level=20.0),
        Ingredient(name="Citric Acid",      quantity=25.0,  unit="kg",  min_stock_level=10.0),
        Ingredient(name="White Vinegar",    quantity=200.0, unit="L",   min_stock_level=50.0),
        Ingredient(name="Garlic Powder",    quantity=15.0,  unit="kg",  min_stock_level=5.0),
        Ingredient(name="Food Preservative E211", quantity=5.0, unit="kg", min_stock_level=2.0),
    ]
    db.add_all(ingredients)
    db.flush()
    prod_map = {p.sku: p.id for p in products}

    # ── Demo Transactions ─────────────────────────────────────────────────────
    admin_id = users[1].id
    emp_id   = users[2].id
    wh_ids   = [w.id for w in warehouses]

    txs = [
        StockTransaction(
            product_id=products[0].id, warehouse_id=wh_ids[1], supplier_id=suppliers[0].id,
            user_id=admin_id, type="stock-in", quantity=200,
            reference_number="PO-2026-001", notes="Initial receipt from Agri-Grow Farms"),
        StockTransaction(
            product_id=products[2].id, warehouse_id=wh_ids[0],
            user_id=emp_id, type="stock-out", quantity=15,
            reference_number="WO-2026-042", notes="Released for Batch 4 Sauce Production"),
        StockTransaction(
            product_id=products[1].id, warehouse_id=wh_ids[2],
            user_id=admin_id, type="adjustment", quantity=-2,
            reference_number="ADJ-009", notes="Damaged during forklift maneuver"),
    ]
    db.add_all(txs)
    db.commit()

print("✅ Seed complete. Default password for all accounts: admin123")
