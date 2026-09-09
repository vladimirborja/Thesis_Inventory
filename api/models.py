"""
api/models.py — SQLAlchemy ORM models (all tables)
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    Integer, String, Text, Numeric, DateTime, Date, ForeignKey,
    CheckConstraint, UniqueConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.database import Base


# ── Users ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:           Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    name:         Mapped[str]            = mapped_column(String(255), nullable=False)
    email:        Mapped[str]            = mapped_column(String(255), unique=True, nullable=False, index=True)
    password:     Mapped[str]            = mapped_column(String(255), nullable=False)
    role:         Mapped[str]            = mapped_column(String(20), nullable=False, default="employee")
    company_name: Mapped[Optional[str]]  = mapped_column(String(255))
    can_input_transactions: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at:   Mapped[datetime]       = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[List["StockTransaction"]] = relationship("StockTransaction", back_populates="user")
    sales:        Mapped[List["Sale"]]             = relationship("Sale", back_populates="user")
    activity:     Mapped[List["ActivityLog"]]      = relationship("ActivityLog", back_populates="user")
    daily_reports: Mapped[List["DailyTransaction"]] = relationship("DailyTransaction", back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN ('super_admin', 'admin', 'employee')", name="ck_user_role"),
    )


# ── Categories ─────────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    name:       Mapped[str]      = mapped_column(String(100), unique=True, nullable=False)
    slug:       Mapped[str]      = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")


# ── Warehouses ─────────────────────────────────────────────────────────────────

class Warehouse(Base):
    __tablename__ = "warehouses"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:       Mapped[str]           = mapped_column(String(255), nullable=False)
    location:   Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[List["StockTransaction"]] = relationship("StockTransaction", back_populates="warehouse")


# ── Suppliers ──────────────────────────────────────────────────────────────────

class Supplier(Base):
    __tablename__ = "suppliers"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:           Mapped[str]           = mapped_column(String(255), nullable=False)
    contact_name:   Mapped[Optional[str]] = mapped_column(String(255))
    email:          Mapped[Optional[str]] = mapped_column(String(255))
    phone:          Mapped[Optional[str]] = mapped_column(String(50))
    address:        Mapped[Optional[str]] = mapped_column(Text)
    lead_time_days: Mapped[int]           = mapped_column(Integer, nullable=False, default=7)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[List["StockTransaction"]] = relationship("StockTransaction", back_populates="supplier")


# ── Products ───────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    category_id:     Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    name:            Mapped[str]           = mapped_column(String(255), nullable=False)
    sku:             Mapped[str]           = mapped_column(String(100), unique=True, nullable=False, index=True)
    barcode:         Mapped[Optional[str]] = mapped_column(String(100), index=True)
    description:     Mapped[Optional[str]] = mapped_column(Text)
    cost_price:      Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    selling_price:   Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    min_stock_level: Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    quantity:        Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    unit_of_measure: Mapped[str]           = mapped_column(String(100), nullable=False, default="pcs")
    lead_time_days:  Mapped[int]           = mapped_column(Integer, nullable=False, default=7)
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    category:     Mapped[Optional["Category"]]          = relationship("Category", back_populates="products")
    images:       Mapped[List["ProductImage"]]          = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    transactions: Mapped[List["StockTransaction"]]      = relationship("StockTransaction", back_populates="product")
    sale_items:   Mapped[List["SaleItem"]]              = relationship("SaleItem", back_populates="product")
    ingredients:  Mapped[List["ProductIngredient"]]     = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")
    forecasts:    Mapped[List["DemandForecast"]]        = relationship("DemandForecast", back_populates="product", cascade="all, delete-orphan")


# ── Product Images ─────────────────────────────────────────────────────────────

class ProductImage(Base):
    __tablename__ = "product_images"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int]           = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    image_url:  Mapped[str]           = mapped_column(Text, nullable=False)
    public_id:  Mapped[Optional[str]] = mapped_column(Text)          # Cloudinary public_id
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="images")


# ── Ingredients ────────────────────────────────────────────────────────────────

class Ingredient(Base):
    __tablename__ = "ingredients"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:            Mapped[str]           = mapped_column(String(255), unique=True, nullable=False)
    quantity:        Mapped[float]         = mapped_column(Numeric(12, 3), nullable=False, default=0)
    unit:            Mapped[Optional[str]] = mapped_column(String(50))
    min_stock_level: Mapped[float]         = mapped_column(Numeric(12, 3), nullable=False, default=0)
    description:     Mapped[Optional[str]] = mapped_column(Text)
    lead_time_days:  Mapped[int]           = mapped_column(Integer, nullable=False, default=7)
    created_at:      Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    product_links: Mapped[List["ProductIngredient"]] = relationship("ProductIngredient", back_populates="ingredient")


# ── Product ↔ Ingredient Recipe ────────────────────────────────────────────────

class ProductIngredient(Base):
    __tablename__ = "product_ingredients"
    __table_args__ = (UniqueConstraint("product_id", "ingredient_id"),)

    id:                Mapped[int]   = mapped_column(Integer, primary_key=True)
    product_id:        Mapped[int]   = mapped_column(Integer, ForeignKey("products.id",    ondelete="CASCADE"))
    ingredient_id:     Mapped[int]   = mapped_column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"))
    quantity_required: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)

    product:    Mapped["Product"]    = relationship("Product",    back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="product_links")


# ── Sales ──────────────────────────────────────────────────────────────────────

class Sale(Base):
    __tablename__ = "sales"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    user_id:        Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount:   Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str]           = mapped_column(String(50), nullable=False, default="cash")
    notes:          Mapped[Optional[str]] = mapped_column(Text)
    created_at:     Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    user:  Mapped["User"]          = relationship("User", back_populates="sales")
    items: Mapped[List["SaleItem"]] = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


# ── Sale Items ─────────────────────────────────────────────────────────────────

class SaleItem(Base):
    __tablename__ = "sale_items"

    id:         Mapped[int]   = mapped_column(Integer, primary_key=True)
    sale_id:    Mapped[int]   = mapped_column(Integer, ForeignKey("sales.id",    ondelete="CASCADE"))
    product_id: Mapped[int]   = mapped_column(Integer, ForeignKey("products.id", ondelete="RESTRICT"))
    quantity:   Mapped[int]   = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    sale:    Mapped["Sale"]    = relationship("Sale",    back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="sale_items")


# ── Stock Transactions ─────────────────────────────────────────────────────────

class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    __table_args__ = (
        CheckConstraint("type IN ('stock-in', 'stock-out', 'adjustment', 'transfer')", name="ck_tx_type"),
    )

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    product_id:       Mapped[int]           = mapped_column(Integer, ForeignKey("products.id"),   nullable=False)
    warehouse_id:     Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("warehouses.id"))
    supplier_id:      Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"))
    user_id:          Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"),      nullable=False)
    type:             Mapped[str]           = mapped_column(String(30), nullable=False)
    quantity:         Mapped[int]           = mapped_column(Integer, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100))
    notes:            Mapped[Optional[str]] = mapped_column(Text)
    created_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    product:   Mapped["Product"]            = relationship("Product",   back_populates="transactions")
    warehouse: Mapped[Optional["Warehouse"]] = relationship("Warehouse", back_populates="transactions")
    supplier:  Mapped[Optional["Supplier"]]  = relationship("Supplier",  back_populates="transactions")
    user:      Mapped["User"]               = relationship("User",      back_populates="transactions")


# ── Activity / Audit Log ───────────────────────────────────────────────────────

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    user_id:     Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    action_type: Mapped[str]           = mapped_column(String(60), nullable=False)
    details:     Mapped[Optional[dict]] = mapped_column(JSON)
    created_at:  Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="activity")


# ── Demand Forecast Snapshots (analytics) ──────────────────────────────────────

class DemandForecast(Base):
    """Persisted forecast outputs for audit / chart history (computed on demand)."""
    __tablename__ = "demand_forecasts"
    __table_args__ = (
        CheckConstraint("period_type IN ('week', 'month')", name="ck_forecast_period"),
    )

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    product_id:         Mapped[int]           = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    period_type:        Mapped[str]           = mapped_column(String(10), nullable=False)  # week | month
    period_key:         Mapped[str]           = mapped_column(String(20), nullable=False)  # e.g. 2026-W12 or 2026-07
    predicted_qty:      Mapped[float]         = mapped_column(Numeric(12, 3), nullable=False, default=0)
    method:             Mapped[str]           = mapped_column(String(60), nullable=False, default="exponential_smoothing")
    mape_percent:       Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    generated_at:       Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    product: Mapped["Product"] = relationship("Product", back_populates="forecasts")


# ── Daily Transaction Reports ──────────────────────────────────────────────────

class DailyTransaction(Base):
    __tablename__ = "daily_transactions"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'submitted')", name="ck_daily_tx_status"),
        UniqueConstraint("user_id", "report_date", name="uq_daily_tx_user_date"),
    )

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    user_id:           Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_date:       Mapped[date]          = mapped_column(Date, nullable=False, index=True)
    client_name:       Mapped[Optional[str]] = mapped_column(String(255))
    total_sales:       Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    cash_collection:   Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    checks_collection: Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    credit_sales:      Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    expenses:          Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    balance:           Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status:            Mapped[str]           = mapped_column(String(20), nullable=False, default="draft")
    notes:             Mapped[Optional[str]] = mapped_column(Text)
    created_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:        Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user:          Mapped["User"]                      = relationship("User", back_populates="daily_reports")
    items:         Mapped[List["DailyTransactionItem"]] = relationship(
        "DailyTransactionItem", back_populates="transaction", cascade="all, delete-orphan",
        order_by="DailyTransactionItem.sort_order",
    )
    denominations: Mapped[Optional["CashDenomination"]] = relationship(
        "CashDenomination", back_populates="transaction", cascade="all, delete-orphan", uselist=False,
    )


class DailyTransactionItem(Base):
    __tablename__ = "daily_transaction_items"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True)
    transaction_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("daily_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    category:          Mapped[str]           = mapped_column(String(100), nullable=False)
    product_name:      Mapped[str]           = mapped_column(String(255), nullable=False)
    weight:            Mapped[Optional[str]] = mapped_column(String(50))
    load_in:           Mapped[Optional[str]] = mapped_column(String(50))
    load_out_bundle:   Mapped[Optional[str]] = mapped_column(String(50))
    load_out_piece:    Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    sales_bundle:      Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    sales_piece:       Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    sales_peso_bundle: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    sales_peso_piece:  Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    total_sales:       Mapped[float]         = mapped_column(Numeric(12, 2), nullable=False, default=0)
    sort_order:        Mapped[int]           = mapped_column(Integer, nullable=False, default=0)

    transaction: Mapped["DailyTransaction"] = relationship("DailyTransaction", back_populates="items")


class CashDenomination(Base):
    __tablename__ = "cash_denominations"

    id:             Mapped[int]   = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int]   = mapped_column(Integer, ForeignKey("daily_transactions.id", ondelete="CASCADE"), unique=True, nullable=False)
    bill_1000:      Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    bill_500:       Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    bill_200:       Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    bill_100:       Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    bill_50:        Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    bill_20:        Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    coins:          Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_amount:   Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    transaction: Mapped["DailyTransaction"] = relationship("DailyTransaction", back_populates="denominations")
