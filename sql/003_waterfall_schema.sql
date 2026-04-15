-- ============================================================
-- Waterfall Yield Schema: Cascading Downgrade System
-- Fish processing value capture — zero waste by design
-- ============================================================

-- ── PRODUCT CATALOGUE (full factory range) ────────────────
DROP TABLE IF EXISTS production.product_catalogue;
CREATE TABLE production.product_catalogue (
    product_code    VARCHAR(20) PRIMARY KEY,
    description     VARCHAR(200) NOT NULL,
    brand           VARCHAR(20) NOT NULL,       -- 'Premium', 'GG', 'ALMARIA'
    species         VARCHAR(20) NOT NULL,       -- 'salmon', 'seabass'
    tier            INT NOT NULL,               -- 1=premium, 2=standard, 3=catch-all
    pack_weight_g   DECIMAL(8,1),               -- final pack weight
    pieces_per_pack INT,
    piece_weight_g  DECIMAL(8,1),               -- individual piece target
    piece_type      VARCHAR(20),                -- 'center_cut', 'tail', 'offcut', 'joint', 'butterfly', 'marinade'
    customer        VARCHAR(50),
    active          BIT DEFAULT 1
);

INSERT INTO production.product_catalogue VALUES
-- Premium (Tier 1 — premium, 120g center-cut only)
('Premium-240',  'Premium Salmon 240g Twin Pack',     'Premium',   'salmon',  1, 240,  2, 120, 'center_cut', 'Retail', 1),
('Premium-480',  'Premium Salmon 480g 4-Piece',       'Premium',   'salmon',  1, 480,  4, 120, 'center_cut', 'Retail', 1),
('Premium-1KG',  'Premium Salmon 1kg',                'Premium',   'salmon',  1, 1000, 8, 120, 'center_cut', 'Retail', 1),
('Premium-J500', 'Premium Salmon Joint 500g',         'Premium',   'salmon',  1, 500,  1, 500, 'joint',      'Retail', 1),

-- GG (Tier 2 — standard, 140g portions + tails + marinades)
('GG-280',     'GG Salmon 280g',                  'GG',      'salmon',  2, 280,  2, 140, 'center_cut', 'Retail', 1),
('GG-240',     'GG Salmon 240g',                  'GG',      'salmon',  2, 240,  2, 120, 'center_cut', 'Retail', 1),
('GG-480',     'GG Salmon 480g 4-Piece',          'GG',      'salmon',  2, 480,  4, 120, 'center_cut', 'Retail', 1),
('GG-J500',    'GG Salmon Joint 500g',            'GG',      'salmon',  2, 500,  1, 500, 'joint',      'Retail', 1),
('GG-FP660',   'Family Pack 660g 6-Piece',        'GG',      'salmon',  2, 660,  6, 110, 'center_cut', 'Retail', 1),
('GG-VP660',   'Vac Pack 660g 6 Fillets',         'GG',      'salmon',  2, 660,  6, 110, 'center_cut', 'Retail', 1),
('GG-SC220',   'Sweet Chilli Marinade 220g',      'GG',      'salmon',  2, 220,  1, 220, 'marinade',   'Retail', 1),
('GG-GH220',   'Garlic & Herb Marinade 220g',     'GG',      'salmon',  2, 220,  1, 220, 'marinade',   'Retail', 1),

-- GG (Tier 3 — catch-all, offcuts)
('GG-SS',      'Simply Salmon 2-10 Pieces',       'GG',      'salmon',  3, NULL, NULL, NULL, 'offcut',  'Retail', 1),

-- ALMARIA (Tier 2 — GG tier, new customer)
('EXP-240',    'Export GG Salmon 240g',          'ALMARIA', 'salmon',  2, 240,  2, 120, 'center_cut', 'Export', 1),
('EXP-SC220',  'Export GG Chilli Marinade 220g', 'ALMARIA', 'salmon',  2, 220,  1, 220, 'marinade',   'Export', 1),
('EXP-SB360',  'Export Seabass 360g',            'ALMARIA', 'seabass', 2, 360,  2, 180, 'center_cut', 'Export', 1),
('EXP-BF255',  'Export Butterfly Seabass 255g',  'ALMARIA', 'seabass', 2, 255,  2, 120, 'butterfly',  'Export', 1);


-- ── INTAKE GRADES ─────────────────────────────────────────
-- Defines what raw material grade can produce what tier
DROP TABLE IF EXISTS production.intake_grades;
CREATE TABLE production.intake_grades (
    grade           VARCHAR(10) PRIMARY KEY,     -- 'Premium', 'GG'
    description     VARCHAR(100),
    max_tier        INT NOT NULL,                -- highest tier this grade can produce
    can_produce_t1  BIT DEFAULT 0,               -- can this go into Premium products?
    can_produce_t2  BIT DEFAULT 1,
    can_produce_t3  BIT DEFAULT 1
);

INSERT INTO production.intake_grades VALUES
('Premium', 'Premium certified salmon — can cascade to all tiers', 1, 1, 1, 1),
('GG',    'Standard grade — Tier 2 and 3 only',                2, 0, 1, 1);


-- ── RUN INPUTS (many batches → one run) ───────────────────
DROP TABLE IF EXISTS production.run_inputs;
CREATE TABLE production.run_inputs (
    input_id        INT IDENTITY PRIMARY KEY,
    run_number      VARCHAR(10) NOT NULL,
    batch_code      VARCHAR(30) NOT NULL,
    grade           VARCHAR(10) NOT NULL,        -- 'Premium' or 'GG'
    species         VARCHAR(20),
    qty_kg          DECIMAL(10,2),
    intake_date     DATE,
    supplier        VARCHAR(100)
);


-- ── RUN OUTPUTS (one run → many products at different tiers)
DROP TABLE IF EXISTS production.run_outputs;
CREATE TABLE production.run_outputs (
    output_id       INT IDENTITY PRIMARY KEY,
    run_number      VARCHAR(10) NOT NULL,
    product_code    VARCHAR(20) NOT NULL,
    tier            INT NOT NULL,
    piece_type      VARCHAR(20),                 -- 'center_cut', 'tail', 'offcut', 'joint'
    qty_packs       INT,
    qty_kg          DECIMAL(10,2),
    source_grade    VARCHAR(10),                 -- what grade went IN
    compliant       BIT DEFAULT 1               -- did grade match tier rules?
);


-- ── BATCH LINEAGE (scan-back tracking) ────────────────────
DROP TABLE IF EXISTS production.batch_lineage;
CREATE TABLE production.batch_lineage (
    lineage_id      INT IDENTITY PRIMARY KEY,
    run_number      VARCHAR(10),
    batch_code      VARCHAR(30),                 -- original batch
    direction       VARCHAR(10) NOT NULL,        -- 'INPUT' or 'SCANBACK'
    qty_kg          DECIMAL(10,2),
    return_method   VARCHAR(20),                 -- 'OCM' (new batch) or 'PROD_RETURN' (same batch)
    new_batch_code  VARCHAR(30),                 -- only if OCM created new batch
    parent_batch    VARCHAR(30),                 -- links new batch to original
    scan_time       DATETIME,
    grade           VARCHAR(10)                  -- preserves grade through lineage
);


-- ── DOWNGRADE LOG (tracks tier movement) ──────────────────
DROP TABLE IF EXISTS production.downgrade_log;
CREATE TABLE production.downgrade_log (
    downgrade_id    INT IDENTITY PRIMARY KEY,
    run_number      VARCHAR(10),
    from_product    VARCHAR(20),                 -- intended product
    to_product      VARCHAR(20),                 -- actual product after downgrade
    from_tier       INT,
    to_tier         INT,
    reason          VARCHAR(50),                 -- 'underweight', 'tail', 'visual', 'light_portion'
    qty_kg          DECIMAL(10,2),
    logged_at       DATETIME DEFAULT GETDATE()
);


-- ── COMPLIANCE RULES (enforced by pipeline) ───────────────
DROP TABLE IF EXISTS production.compliance_rules;
CREATE TABLE production.compliance_rules (
    rule_id         INT PRIMARY KEY,
    rule_name       VARCHAR(100),
    check_sql       VARCHAR(500),
    severity        VARCHAR(10),                 -- 'CRITICAL', 'MAJOR', 'MINOR'
    description     VARCHAR(500)
);

INSERT INTO production.compliance_rules VALUES
(1, 'NO_GG_IN_Premium',
   'SELECT * FROM run_outputs WHERE source_grade = ''GG'' AND tier = 1',
   'CRITICAL', 'GG grade material packed into Premium Tier 1 product'),
(2, 'NO_TAILS_IN_Premium',
   'SELECT * FROM run_outputs WHERE piece_type = ''tail'' AND tier = 1',
   'CRITICAL', 'Tail pieces packed into Premium product'),
(3, 'SPECIES_MISMATCH',
   'SELECT o.* FROM run_outputs o JOIN product_catalogue p ON o.product_code = p.product_code JOIN run_inputs i ON o.run_number = i.run_number WHERE i.species != p.species',
   'CRITICAL', 'Salmon batch packed into seabass product or vice versa'),
(4, 'SIMPLY_SALMON_NOT_Premium',
   'SELECT * FROM run_outputs WHERE product_code = ''GG-SS'' AND source_grade = ''Premium'' AND tier != 3',
   'MAJOR', 'Simply Salmon must always be GG tier 3');
