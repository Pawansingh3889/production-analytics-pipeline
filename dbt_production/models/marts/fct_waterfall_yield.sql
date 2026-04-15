-- Mart: waterfall yield analysis — value captured per tier
-- Shows how much of each run went to premium vs standard vs catch-all
-- This is the financial yield, not just physical yield

SELECT
    r.run_number,
    r.production_date,
    r.shift_code,

    -- Input totals
    SUM(DISTINCT r.target_qty_kg) AS input_kg,

    -- Tier 1 (Premium premium)
    SUM(CASE WHEN o.tier = 1 THEN o.qty_kg ELSE 0 END) AS tier1_kg,
    ROUND(
        SUM(CASE WHEN o.tier = 1 THEN o.qty_kg ELSE 0 END) /
        NULLIF(SUM(DISTINCT r.target_qty_kg), 0) * 100, 1
    ) AS tier1_pct,

    -- Tier 2 (GG standard + marinades)
    SUM(CASE WHEN o.tier = 2 THEN o.qty_kg ELSE 0 END) AS tier2_kg,
    ROUND(
        SUM(CASE WHEN o.tier = 2 THEN o.qty_kg ELSE 0 END) /
        NULLIF(SUM(DISTINCT r.target_qty_kg), 0) * 100, 1
    ) AS tier2_pct,

    -- Tier 3 (Simply Salmon catch-all)
    SUM(CASE WHEN o.tier = 3 THEN o.qty_kg ELSE 0 END) AS tier3_kg,
    ROUND(
        SUM(CASE WHEN o.tier = 3 THEN o.qty_kg ELSE 0 END) /
        NULLIF(SUM(DISTINCT r.target_qty_kg), 0) * 100, 1
    ) AS tier3_pct,

    -- Total captured (all tiers)
    SUM(o.qty_kg) AS total_captured_kg,
    ROUND(
        SUM(o.qty_kg) / NULLIF(SUM(DISTINCT r.target_qty_kg), 0) * 100, 1
    ) AS capture_rate_pct,

    -- True waste (input - all tiers)
    SUM(DISTINCT r.target_qty_kg) - SUM(o.qty_kg) AS true_waste_kg,

    -- Compliance
    MIN(o.compliant) AS all_compliant

FROM {{ ref('stg_runs') }} r
LEFT JOIN {{ ref('stg_run_outputs') }} o ON r.run_number = o.run_number
WHERE r.status = 'complete'
GROUP BY r.run_number, r.production_date, r.shift_code
