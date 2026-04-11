-- Mart: product mix analysis — what did each run actually produce?
-- Shows the cascade: how much went to each product from each run

SELECT
    o.run_number,
    r.production_date,
    p.brand,
    p.description AS product,
    p.tier,
    p.piece_type,
    p.pack_weight_g,
    o.qty_packs,
    o.qty_kg,
    o.source_grade,
    ROUND(
        o.qty_kg / NULLIF(SUM(o.qty_kg) OVER (PARTITION BY o.run_number), 0) * 100, 1
    ) AS pct_of_run
FROM {{ ref('stg_run_outputs') }} o
LEFT JOIN {{ ref('stg_runs') }} r ON o.run_number = r.run_number
LEFT JOIN {{ source('production', 'product_catalogue') }} p ON o.product_code = p.product_code
ORDER BY o.run_number, p.tier, o.qty_kg DESC
