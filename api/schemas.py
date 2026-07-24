"""
api/schemas.py — Pydantic v2 request/response schemas

All response schemas use alias_generator=to_camel so the JSON output is
camelCase — matching the existing TypeScript frontend types.
"""

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.alias_generators import to_camel


# ── Base ───────────────────────────────────────────────────────────────────────

class CamelModel(BaseModel):
    """
    Base class for response schemas.
    - from_attributes: reads from SQLAlchemy ORM objects
    - alias_generator: serialises snake_case fields as camelCase
    - populate_by_name: also accepts the original snake_case name on input
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "employee"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"super_admin", "admin", "employee"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(CamelModel):
    id: int
    name: str
    email: str
    role: str
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Categories ─────────────────────────────────────────────────────────────────

class CategoryResponse(CamelModel):
    id: int
    name: str
    slug: str


# ── Warehouses ─────────────────────────────────────────────────────────────────

class WarehouseResponse(CamelModel):
    id: int
    name: str
    location: Optional[str] = None


# ── Suppliers ──────────────────────────────────────────────────────────────────

class SupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = 7


class SupplierUpdate(SupplierCreate):
    name: Optional[str] = None
    lead_time_days: Optional[int] = None


class SupplierResponse(CamelModel):
    id: int
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = 7
    created_at: Optional[datetime] = None


# ── Products ───────────────────────────────────────────────────────────────────

class ProductImageResponse(CamelModel):
    id: int
    image_url: str
    created_at: Optional[datetime] = None


class ProductCreate(BaseModel):
    name: str
    sku: str
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    cost_price: float = 0
    selling_price: float = 0
    min_stock_level: int = 0
    quantity: int = 0
    unit_of_measure: str = "pcs"
    lead_time_days: int = 7


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    min_stock_level: Optional[int] = None
    quantity: Optional[int] = None
    unit_of_measure: Optional[str] = None
    lead_time_days: Optional[int] = None


class ProductResponse(CamelModel):
    id: int
    name: str
    sku: str
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    description: Optional[str] = None
    cost_price: float
    selling_price: float
    min_stock_level: int
    quantity: int
    unit_of_measure: str
    lead_time_days: int = 7
    created_at: Optional[datetime] = None
    images: List[ProductImageResponse] = []

    @classmethod
    def from_orm_with_category(cls, product: Any) -> "ProductResponse":
        obj = cls.model_validate(product)
        if product.category:
            obj.category_name = product.category.name
        return obj


# ── Ingredients ────────────────────────────────────────────────────────────────

class IngredientCreate(BaseModel):
    name: str
    quantity: float = 0
    unit: Optional[str] = None
    min_stock_level: float = 0
    description: Optional[str] = None
    lead_time_days: int = 7


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    min_stock_level: Optional[float] = None
    description: Optional[str] = None
    lead_time_days: Optional[int] = None


class IngredientResponse(CamelModel):
    id: int
    name: str
    quantity: float
    unit: Optional[str] = None
    min_stock_level: float
    description: Optional[str] = None
    lead_time_days: int = 7
    created_at: Optional[datetime] = None


# ── Sales ──────────────────────────────────────────────────────────────────────

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class SaleCreate(BaseModel):
    payment_method: str = "cash"
    notes: Optional[str] = None
    items: List[SaleItemCreate]


class SaleItemResponse(CamelModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product_name: Optional[str] = None


class SaleResponse(CamelModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    total_amount: float
    payment_method: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[SaleItemResponse] = []


# ── Stock Transactions ─────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    product_id: int
    warehouse_id: Optional[int] = None
    supplier_id: Optional[int] = None
    type: str
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"stock-in", "stock-out", "adjustment", "transfer"}
        if v not in allowed:
            raise ValueError(f"Type must be one of {allowed}")
        return v


class TransactionResponse(CamelModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    warehouse_id: Optional[int] = None
    warehouse_name: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    type: str
    quantity: int
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


# ── Users (admin management) ───────────────────────────────────────────────────

class UserUpdateRole(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"super_admin", "admin", "employee"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v


# ── Activity Logs ──────────────────────────────────────────────────────────────

class ActivityLogResponse(CamelModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    action_type: str
    details: Optional[Any] = None
    created_at: Optional[datetime] = None


# ── Dashboard (super admin) ────────────────────────────────────────────────────

class DashboardSummaryResponse(CamelModel):
    total_users: int
    total_buy: float
    total_sell: float


class MonthlySalesItem(CamelModel):
    month: str          # YYYY-MM
    label: str          # e.g. "Jan 2026"
    total: float


# ── Analytics / IE decision support ────────────────────────────────────────────

class ForecastHistoryPoint(CamelModel):
    period: str
    label: str
    actual: float
    fitted: Optional[float] = None


class ForecastPoint(CamelModel):
    period: str
    label: str
    predicted: float


class ProductForecastResponse(CamelModel):
    product_id: int
    product_name: str
    sku: str
    period: str
    horizon: int
    method: str
    alpha: Optional[float] = None
    mape_percent: Optional[float] = None
    next_period_demand: float
    history: List[ForecastHistoryPoint] = []
    forecast: List[ForecastPoint] = []


class AbcItem(CamelModel):
    product_id: int
    name: str
    sku: str
    sales_value: float
    value_share_percent: float
    cumulative_percent: float
    abc_class: str


class AbcAnalysisResponse(CamelModel):
    items: List[AbcItem]
    counts: dict


class ReorderPointItem(CamelModel):
    item_type: str  # product | ingredient
    item_id: int
    name: str
    sku: Optional[str] = None
    avg_daily_usage: float
    demand_std_dev: float
    lead_time_days: int
    z_score: float
    safety_stock: float
    reorder_point: float
    recommended_order_qty: int
    current_quantity: float
    min_stock_level: float
    below_rop: bool
    below_min_stock: bool
    needs_reorder: bool


class AnalyticsOverviewResponse(CamelModel):
    products_below_rop: int
    ingredients_below_rop: int
    class_a_count: int
    class_b_count: int
    class_c_count: int
    avg_mape_percent: Optional[float] = None
    lead_time_days_default: int


# ── Generic paginated wrapper ──────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]
