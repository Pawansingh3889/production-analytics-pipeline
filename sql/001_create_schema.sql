-- ============================================================
-- Fish Production ERP Schema (Mock)
-- Based on SI Integreater OCM module patterns
-- ============================================================

CREATE SCHEMA IF NOT EXISTS production;

-- ── PRODUCTION LINES ──────────────────────────────────────
CREATE TABLE production.prod_lines (
    line_id         INT PRIMARY KEY,
    line_name       VARCHAR(50) NOT NULL,       -- 'Line 1', 'Line 2', 'Packing A'
    line_type       VARCHAR(30),                -- 'filleting', 'packing', 'smoking'
    area            VARCHAR(30),                -- 'fresh', 'smoked', 'value-added'
    max_capacity_kg DECIMAL(10,2),
    active          BIT DEFAULT 1,
    created_date    DATETIME DEFAULT GETDATE()
);

-- ── PRODUCTS / PLU (Price Look-Up) ────────────────────────
CREATE TABLE production.products (
    product_code    VARCHAR(20) PRIMARY KEY,     -- matches SI_OCM_PLU
    description     VARCHAR(200) NOT NULL,
    category        VARCHAR(50),                 -- 'cod fillet', 'salmon portion', 'fish cake'
    species         VARCHAR(50),                 -- 'cod', 'salmon', 'haddock', 'mackerel'
    customer        VARCHAR(50),                 -- 'Lidl', 'Iceland', 'Tesco', 'M&S'
    pack_size_g     DECIMAL(8,2),
    shelf_life_days INT,
    allergens       VARCHAR(200),                -- 'fish, mustard, sulphites'
    hazard_class    VARCHAR(10),                 -- 'HIGH', 'MEDIUM', 'LOW'
    active          BIT DEFAULT 1,
    created_date    DATETIME DEFAULT GETDATE(),
    updated_date    DATETIME
);

-- ── PRODUCTION RUNS ───────────────────────────────────────
CREATE TABLE production.runs (
    run_number      VARCHAR(10) PRIMARY KEY,     -- '003215', '004273' etc
    production_date DATE NOT NULL,
    shift_code      VARCHAR(5),                  -- 'DAY', 'NIGHT', 'LATE'
    shift_date      DATE,
    prod_line       INT REFERENCES production.prod_lines(line_id),
    product_code    VARCHAR(20) REFERENCES production.products(product_code),
    spec            VARCHAR(50),                 -- product specification ref
    prog_id         VARCHAR(20),                 -- programme/recipe ID
    target_qty_kg   DECIMAL(10,2),
    actual_qty_kg   DECIMAL(10,2),
    waste_kg        DECIMAL(10,2) DEFAULT 0,
    yield_pct       DECIMAL(5,2),                -- actual/target * 100
    status          VARCHAR(20) DEFAULT 'active', -- 'active', 'complete', 'cancelled'
    complete        BIT DEFAULT 0,
    bh_time         DATETIME,                    -- best before / use by time
    kill_date       DATE,                        -- raw material kill date (traceability)
    trace_id        VARCHAR(30),                 -- traceability batch reference
    created_by      VARCHAR(50),
    created_date    DATETIME DEFAULT GETDATE(),
    updated_by      VARCHAR(50),
    updated_date    DATETIME
);

-- ── PRODUCTION TRANSACTIONS (per-pack weights) ────────────
CREATE TABLE production.transactions (
    trans_id        BIGINT IDENTITY PRIMARY KEY,  -- matches SI_OCM_TRANS
    run_number      VARCHAR(10) REFERENCES production.runs(run_number),
    trans_date      DATETIME NOT NULL,
    product_code    VARCHAR(20),
    weight_g        DECIMAL(8,2) NOT NULL,        -- individual pack weight
    target_weight_g DECIMAL(8,2),
    tare_g          DECIMAL(6,2) DEFAULT 0,       -- packaging tare weight
    net_weight_g    DECIMAL(8,2),                  -- weight - tare
    overweight_g    DECIMAL(6,2),                  -- net - target (giveaway)
    barcode         VARCHAR(30),
    label_printed   BIT DEFAULT 1,
    scanner_pass    BIT DEFAULT 1,                 -- inline scanner check
    prod_line       INT,
    operator_id     VARCHAR(20)
);

-- ── PRODUCTION TOTALS (shift/run aggregates) ──────────────
CREATE TABLE production.run_totals (
    run_number      VARCHAR(10) REFERENCES production.runs(run_number),
    total_packs     INT,
    total_weight_kg DECIMAL(10,2),
    avg_weight_g    DECIMAL(8,2),
    min_weight_g    DECIMAL(8,2),
    max_weight_g    DECIMAL(8,2),
    std_dev_g       DECIMAL(6,2),
    giveaway_kg     DECIMAL(8,2),                  -- total overweight
    giveaway_pct    DECIMAL(5,2),
    reject_count    INT DEFAULT 0,
    downtime_mins   INT DEFAULT 0,
    updated_date    DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (run_number)
);

-- ── TRACEABILITY ──────────────────────────────────────────
CREATE TABLE production.traceability (
    trace_id        VARCHAR(30) PRIMARY KEY,
    batch_code      VARCHAR(30) NOT NULL,
    supplier        VARCHAR(100),
    species         VARCHAR(50),
    catch_area      VARCHAR(50),                   -- FAO area: 'North Sea', 'Atlantic'
    catch_method    VARCHAR(50),                   -- 'trawl', 'line caught', 'farmed'
    vessel_name     VARCHAR(100),
    landing_date    DATE,
    kill_date       DATE,
    received_date   DATE,
    received_temp_c DECIMAL(4,1),                  -- goods-in temperature
    use_by_date     DATE,
    country_origin  VARCHAR(50),
    certified       VARCHAR(50),                   -- 'MSC', 'ASC', 'none'
    allergen_check  BIT DEFAULT 0,
    created_date    DATETIME DEFAULT GETDATE()
);

-- ── TEMPERATURE MONITORING ────────────────────────────────
CREATE TABLE production.temperature_logs (
    log_id          BIGINT IDENTITY PRIMARY KEY,
    location        VARCHAR(50) NOT NULL,          -- 'chiller_1', 'blast_freezer', 'goods_in'
    reading_time    DATETIME NOT NULL,
    temp_celsius    DECIMAL(4,1) NOT NULL,
    target_min      DECIMAL(4,1) DEFAULT -1.0,
    target_max      DECIMAL(4,1) DEFAULT 4.0,
    in_range        BIT,                           -- auto-calculated
    alert_raised    BIT DEFAULT 0,
    recorded_by     VARCHAR(50)
);

-- ── NON-CONFORMANCE / QUALITY ─────────────────────────────
CREATE TABLE production.non_conformance (
    nc_id           INT IDENTITY PRIMARY KEY,
    nc_date         DATE NOT NULL,
    run_number      VARCHAR(10),
    product_code    VARCHAR(20),
    nc_type         VARCHAR(50),                   -- 'weight', 'label', 'foreign_body', 'temp'
    severity        VARCHAR(10),                   -- 'critical', 'major', 'minor'
    description     VARCHAR(500),
    root_cause      VARCHAR(500),
    corrective_action VARCHAR(500),
    raised_by       VARCHAR(50),
    closed_by       VARCHAR(50),
    closed_date     DATE,
    status          VARCHAR(20) DEFAULT 'open'     -- 'open', 'investigating', 'closed'
);

-- ── CASE VERIFICATION (inline scanner) ────────────────────
CREATE TABLE production.case_verification (
    verify_id       BIGINT IDENTITY PRIMARY KEY,
    run_number      VARCHAR(10),
    case_barcode    VARCHAR(30),
    expected_plu    VARCHAR(20),
    scanned_plu     VARCHAR(20),
    match           BIT,                           -- expected = scanned
    scan_time       DATETIME,
    scanner_id      VARCHAR(20),
    prod_line       INT
);

-- ── DESPATCH / ORDERS ─────────────────────────────────────
CREATE TABLE production.despatch (
    despatch_id     INT IDENTITY PRIMARY KEY,
    order_number    VARCHAR(20),
    customer        VARCHAR(50),
    product_code    VARCHAR(20),
    qty_cases       INT,
    qty_kg          DECIMAL(10,2),
    despatch_date   DATE,
    delivery_date   DATE,
    vehicle_temp_c  DECIMAL(4,1),
    status          VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'loaded', 'delivered'
);

-- ── SHIFTS / LABOUR ───────────────────────────────────────
CREATE TABLE production.shifts (
    shift_id        INT IDENTITY PRIMARY KEY,
    shift_date      DATE NOT NULL,
    shift_code      VARCHAR(5) NOT NULL,           -- 'DAY', 'NIGHT'
    line_id         INT,
    headcount       INT,
    planned_hours   DECIMAL(6,2),
    actual_hours    DECIMAL(6,2),
    overtime_hours  DECIMAL(6,2) DEFAULT 0,
    output_kg       DECIMAL(10,2),
    kg_per_head     DECIMAL(8,2)                   -- productivity KPI
);
