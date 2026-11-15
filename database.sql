-- =============================================================================
--  IMS PostgreSQL Schema
--  Run this in your Neon / Supabase SQL editor to set up tables.
--  Demo seed data is inserted by scripts/seed.py
-- =============================================================================

-- Drop in reverse dependency order (idempotent re-run)
DROP TABLE IF EXISTS cash_denominations       CASCADE;
DROP TABLE IF EXISTS daily_transaction_items  CASCADE;
DROP TABLE IF EXISTS daily_transactions       CASCADE;
DROP TABLE IF EXISTS demand_forecasts   CASCADE;
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
    can_input_transactions BOOLEAN NOT NULL DEFAULT FALSE,
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
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    contact_name   VARCHAR(255),
    email          VARCHAR(255),
    phone          VARCHAR(50),
    address        TEXT,
    lead_time_days INT NOT NULL DEFAULT 7,
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    lead_time_days  INT            NOT NULL DEFAULT 7,
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
    lead_time_days  INT NOT NULL DEFAULT 7,
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

-- ── Daily Transaction Reports (employee field sales) ────────────────────────────
CREATE TABLE daily_transactions (
    id                SERIAL PRIMARY KEY,
    user_id           INT            NOT NULL REFERENCES users(id),
    report_date       DATE           NOT NULL,
    client_name       VARCHAR(255),
    total_sales       NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cash_collection   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    checks_collection NUMERIC(12, 2) NOT NULL DEFAULT 0,
    credit_sales      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    expenses          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    balance           NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status            VARCHAR(20)    NOT NULL DEFAULT 'draft'
                          CHECK (status IN ('draft', 'submitted')),
    notes             TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, report_date)
);

CREATE TABLE daily_transaction_items (
    id                 SERIAL PRIMARY KEY,
    transaction_id     INT            NOT NULL REFERENCES daily_transactions(id) ON DELETE CASCADE,
    category           VARCHAR(100)   NOT NULL,
    product_name       VARCHAR(255)   NOT NULL,
    weight             VARCHAR(50),
    load_in            VARCHAR(50),
    load_out_bundle    VARCHAR(50),
    load_out_piece     NUMERIC(12, 3),
    sales_bundle       NUMERIC(12, 3),
    sales_piece        NUMERIC(12, 3),
    sales_peso_bundle  NUMERIC(12, 2),
    sales_peso_piece   NUMERIC(12, 2),
    total_sales        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    sort_order         INT            NOT NULL DEFAULT 0
);

CREATE TABLE cash_denominations (
    id             SERIAL PRIMARY KEY,
    transaction_id INT            NOT NULL UNIQUE REFERENCES daily_transactions(id) ON DELETE CASCADE,
    bill_1000      INT            NOT NULL DEFAULT 0,
    bill_500       INT            NOT NULL DEFAULT 0,
    bill_200       INT            NOT NULL DEFAULT 0,
    bill_100       INT            NOT NULL DEFAULT 0,
    bill_50        INT            NOT NULL DEFAULT 0,
    bill_20        INT            NOT NULL DEFAULT 0,
    coins          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_amount   NUMERIC(12, 2) NOT NULL DEFAULT 0
);

-- ── Demand Forecast Snapshots (analytics) ─────────────────────────────────────
CREATE TABLE demand_forecasts (
    id            SERIAL PRIMARY KEY,
    product_id    INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    period_type   VARCHAR(10) NOT NULL
                      CHECK (period_type IN ('week', 'month')),
    period_key    VARCHAR(20) NOT NULL,          -- e.g. 2026-W12 or 2026-07
    predicted_qty NUMERIC(12, 3) NOT NULL DEFAULT 0,
    method        VARCHAR(60) NOT NULL DEFAULT 'exponential_smoothing',
    mape_percent  NUMERIC(8, 2),
    generated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
CREATE INDEX idx_sale_items_product   ON sale_items(product_id);
CREATE INDEX idx_forecasts_product    ON demand_forecasts(product_id);
CREATE INDEX idx_forecasts_generated  ON demand_forecasts(generated_at DESC);
CREATE INDEX idx_forecasts_period     ON demand_forecasts(period_type, period_key);
CREATE INDEX idx_daily_tx_user        ON daily_transactions(user_id);
CREATE INDEX idx_daily_tx_date        ON daily_transactions(report_date DESC);
CREATE INDEX idx_daily_tx_status      ON daily_transactions(status);
CREATE INDEX idx_daily_items_tx       ON daily_transaction_items(transaction_id);

-- =============================================================================
-- INCREMENTAL MIGRATION (safe for existing Neon / production data)
-- Copy ONLY the block below into your SQL editor if tables already exist.
-- No DROP statements — additive only.
-- =============================================================================
-- BEGIN INCREMENTAL
ALTER TABLE suppliers
    ADD COLUMN IF NOT EXISTS lead_time_days INT NOT NULL DEFAULT 7;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS lead_time_days INT NOT NULL DEFAULT 7;

ALTER TABLE ingredients
    ADD COLUMN IF NOT EXISTS lead_time_days INT NOT NULL DEFAULT 7;

CREATE TABLE IF NOT EXISTS demand_forecasts (
    id            SERIAL PRIMARY KEY,
    product_id    INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    period_type   VARCHAR(10) NOT NULL
                      CHECK (period_type IN ('week', 'month')),
    period_key    VARCHAR(20) NOT NULL,
    predicted_qty NUMERIC(12, 3) NOT NULL DEFAULT 0,
    method        VARCHAR(60) NOT NULL DEFAULT 'exponential_smoothing',
    mape_percent  NUMERIC(8, 2),
    generated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sale_items_product  ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_product   ON demand_forecasts(product_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_generated ON demand_forecasts(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_forecasts_period    ON demand_forecasts(period_type, period_key);

CREATE TABLE IF NOT EXISTS daily_transactions (
    id                SERIAL PRIMARY KEY,
    user_id           INT            NOT NULL REFERENCES users(id),
    report_date       DATE           NOT NULL,
    client_name       VARCHAR(255),
    total_sales       NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cash_collection   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    checks_collection NUMERIC(12, 2) NOT NULL DEFAULT 0,
    credit_sales      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    expenses          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    balance           NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status            VARCHAR(20)    NOT NULL DEFAULT 'draft'
                          CHECK (status IN ('draft', 'submitted')),
    notes             TEXT,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, report_date)
);

CREATE TABLE IF NOT EXISTS daily_transaction_items (
    id                 SERIAL PRIMARY KEY,
    transaction_id     INT            NOT NULL REFERENCES daily_transactions(id) ON DELETE CASCADE,
    category           VARCHAR(100)   NOT NULL,
    product_name       VARCHAR(255)   NOT NULL,
    weight             VARCHAR(50),
    load_in            VARCHAR(50),
    load_out_bundle    VARCHAR(50),
    load_out_piece     NUMERIC(12, 3),
    sales_bundle       NUMERIC(12, 3),
    sales_piece        NUMERIC(12, 3),
    sales_peso_bundle  NUMERIC(12, 2),
    sales_peso_piece   NUMERIC(12, 2),
    total_sales        NUMERIC(12, 2) NOT NULL DEFAULT 0,
    sort_order         INT            NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cash_denominations (
    id             SERIAL PRIMARY KEY,
    transaction_id INT            NOT NULL UNIQUE REFERENCES daily_transactions(id) ON DELETE CASCADE,
    bill_1000      INT            NOT NULL DEFAULT 0,
    bill_500       INT            NOT NULL DEFAULT 0,
    bill_200       INT            NOT NULL DEFAULT 0,
    bill_100       INT            NOT NULL DEFAULT 0,
    bill_50        INT            NOT NULL DEFAULT 0,
    bill_20        INT            NOT NULL DEFAULT 0,
    coins          NUMERIC(12, 2) NOT NULL DEFAULT 0,
    total_amount   NUMERIC(12, 2) NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_daily_tx_user   ON daily_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_tx_date   ON daily_transactions(report_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_tx_status ON daily_transactions(status);
CREATE INDEX IF NOT EXISTS idx_daily_items_tx  ON daily_transaction_items(transaction_id);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS can_input_transactions BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS avatar_url TEXT;
-- END INCREMENTAL
-- =============================================================================
