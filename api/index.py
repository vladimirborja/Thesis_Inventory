"""
api/index.py — FastAPI application entry point (Vercel serverless)

Vercel looks for `app` at module level in api/index.py.
All /api/* routes are handled here; Vue SPA is served from dist/ statically.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # local dev only — Vercel injects env vars directly

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routers import (
    auth, products, suppliers, warehouses,
    transactions, ingredients, sales, users, activity, categories
)

# ── Lifespan (create tables on first cold-start if needed) ─────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables should already exist (created via database.sql + seed.py),
    # but this is a safe guard for the very first deploy.
    from api.database import engine
    from api.models import Base
    Base.metadata.create_all(bind=engine)
    yield


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Apex IMS API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── Rate limiting ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────────
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler — always return JSON ──────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )

# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/auth",         tags=["Auth"])
app.include_router(products.router,     prefix="/api/products",     tags=["Products"])
app.include_router(categories.router,   prefix="/api/categories",   tags=["Categories"])
app.include_router(suppliers.router,    prefix="/api/suppliers",    tags=["Suppliers"])
app.include_router(warehouses.router,   prefix="/api/warehouses",   tags=["Warehouses"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(ingredients.router,  prefix="/api/ingredients",  tags=["Ingredients"])
app.include_router(sales.router,        prefix="/api/sales",        tags=["Sales"])
app.include_router(users.router,        prefix="/api/users",        tags=["Users"])
app.include_router(activity.router,     prefix="/api/activity",     tags=["Activity"])
