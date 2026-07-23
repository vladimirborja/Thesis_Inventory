-- =============================================================================
--  IMS PostgreSQL Schema
--  Run this in your Neon / Supabase SQL editor to set up tables.
--  Demo seed data is inserted by scripts/seed.py
-- =============================================================================

-- Drop in reverse dependency order (idempotent re-run)
DROP TABLE IF EXISTS activity_logs      CASCADE;
DROP TABLE IF EXISTS sale_items         CASCADE;
DROP TABLE IF EXISTS sales              CASCADE;
DROP TABLE IF EXISTS product_ingredients CASCADE;
DROP TABLE IF EXISTS product_images     CASCADE;
DROP TABLE IF EXISTS stock_transactions CASCADE;
DROP TABLE IF EXISTS products           CASCADE;
DROP TABLE IF EXISTS ingredients        CASCADE;
DROP TABLE IF EXISTS suppliers          CASCADE;
DROP TABLE IF EXISTS warehouses         CASCADE;
DROP TABLE IF EXISTS categories         CASCADE;
DROP TABLE IF EXISTS users              CASCADE;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255)        NOT NULL,
    email        VARCHAR(255) UNIQUE NOT NULL,
    password     VARCHAR(255)        NOT NULL,     -- bcrypt hash
    role         VARCHAR(20)         NOT NULL DEFAULT 'employee'
                     CHECK (role IN ('super_admin', 'admin', 'employee')),
    company_name VARCHAR(255),
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Categories ────────────────────────────────────────────────────────────────
CREATE TABLE categories (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) UNIQUE NOT NULL,
    slug       VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Warehouses ────────────────────────────────────────────────────────────────
CREATE TABLE warehouses (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    location   TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Suppliers ─────────────────────────────────────────────────────────────────
CREATE TABLE suppliers (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email        VARCHAR(255),
    phone        VARCHAR(50),
    address      TEXT,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Products ──────────────────────────────────────────────────────────────────
CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    category_id     INT REFERENCES categories(id) ON DELETE SET NULL,
    name            VARCHAR(255) NOT NULL,
    sku             VARCHAR(100) UNIQUE NOT NULL,
    barcode         VARCHAR(100),
    description     TEXT,
    cost_price      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    selling_price   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    min_stock_level INT            NOT NULL DEFAULT 0,
    quantity        INT            NOT NULL DEFAULT 0,
    unit_of_measure VARCHAR(100)   NOT NULL DEFAULT 'pcs',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Product Verification Images ───────────────────────────────────────────────
CREATE TABLE product_images (
    id         SERIAL PRIMARY KEY,
    product_id INT  NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url  TEXT NOT NULL,             -- Cloudinary secure URL
    public_id  TEXT,                      -- Cloudinary public_id (for deletion)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Ingredients ───────────────────────────────────────────────────────────────
CREATE TABLE ingredients (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) UNIQUE NOT NULL,
    quantity        NUMERIC(12, 3) NOT NULL DEFAULT 0,
    unit            VARCHAR(50),
    min_stock_level NUMERIC(12, 3)   NOT NULL DEFAULT 0,
    description     TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Product ↔ Ingredient Recipe ───────────────────────────────────────────────
CREATE TABLE product_ingredients (
    id                SERIAL PRIMARY KEY,
    product_id        INT            NOT NULL REFERENCES products(id)    ON DELETE CASCADE,
    ingredient_id     INT            NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    quantity_required NUMERIC(12, 3) NOT NULL,    -- amount consumed per 1 unit produced
    UNIQUE (product_id, ingredient_id)
);

-- ── Sales ─────────────────────────────────────────────────────────────────────
CREATE TABLE sales (
    id             SERIAL PRIMARY KEY,
    user_id        INT            NOT NULL REFERENCES users(id),
    total_amount   NUMERIC(12, 2) NOT NULL,
    payment_method VARCHAR(50)    NOT NULL DEFAULT 'cash',
    notes          TEXT,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Sale Line Items ───────────────────────────────────────────────────────────
CREATE TABLE sale_items (
    id         SERIAL PRIMARY KEY,
    sale_id    INT            NOT NULL REFERENCES sales(id)    ON DELETE CASCADE,
    product_id INT            NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity   INT            NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL
);

-- ── Stock Transactions ────────────────────────────────────────────────────────
CREATE TABLE stock_transactions (
    id               SERIAL PRIMARY KEY,
    product_id       INT NOT NULL REFERENCES products(id),
    warehouse_id     INT REFERENCES warehouses(id),
    supplier_id      INT REFERENCES suppliers(id),
    user_id          INT NOT NULL REFERENCES users(id),
    type             VARCHAR(30) NOT NULL
                         CHECK (type IN ('stock-in', 'stock-out', 'adjustment', 'transfer')),
    quantity         INT  NOT NULL,
    reference_number VARCHAR(100),
    notes            TEXT,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Activity / Audit Log ──────────────────────────────────────────────────────
CREATE TABLE activity_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INT         NOT NULL REFERENCES users(id),
    action_type VARCHAR(60) NOT NULL,   -- e.g. stock-in | sale | product-create
    details     JSONB,                  -- flexible payload
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX idx_products_sku         ON products(sku);
CREATE INDEX idx_products_barcode     ON products(barcode);
CREATE INDEX idx_transactions_product ON stock_transactions(product_id);
CREATE INDEX idx_transactions_user    ON stock_transactions(user_id);
CREATE INDEX idx_activity_user        ON activity_logs(user_id);
CREATE INDEX idx_activity_created     ON activity_logs(created_at DESC);
CREATE INDEX idx_sales_user           ON sales(user_id);
CREATE INDEX idx_sales_created        ON sales(created_at DESC);
