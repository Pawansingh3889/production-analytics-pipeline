-- Mart: daily yield and waste analysis per line and product
-- Key KPI for production managers and BRC auditors

SELECT
    r.production_date,
    r.shift_code,
    r.prod_line,
    p.description AS product_name,
    p.species,
    p.customer,
    COUNT(*) AS run_count,
    SUM(r.target_qty_kg) AS total_target_kg,
    SUM(r.actual_qty_kg) AS total_actual_kg,
    SUM(r.waste_kg) AS total_waste_kg,
    ROUND(AVG(r.yield_pct), 1) AS avg_yield_pct,
    ROUND(
        SUM(r.waste_kg) / NULLIF(SUM(r.target_qty_kg), 0) * 100, 1
    ) AS waste_pct,
    ROUND(
        SUM(r.actual_qty_kg) / NULLIF(SUM(r.target_qty_kg), 0) * 100, 1
    ) AS efficiency_pct
FROM {{ ref('stg_runs') }} r
LEFT JOIN {{ source('production', 'products') }} p
    ON r.product_code = p.product_code
WHERE r.status = 'complete'
GROUP BY
    r.production_date,
    r.shift_code,
    r.prod_line,
    p.description,
    p.species,
    p.customer
