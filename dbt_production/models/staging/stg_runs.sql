-- Staging: clean production run data
SELECT
    run_number,
    production_date,
    UPPER(TRIM(shift_code)) AS shift_code,
    prod_line,
    TRIM(product_code) AS product_code,
    target_qty_kg,
    actual_qty_kg,
    waste_kg,
    CASE
        WHEN target_qty_kg > 0 AND actual_qty_kg IS NOT NULL
        THEN ROUND(actual_qty_kg / target_qty_kg * 100, 1)
        ELSE NULL
    END AS yield_pct,
    trace_id,
    kill_date,
    status,
    complete,
    created_by AS operator,
    created_date
FROM {{ source('production', 'runs') }}
WHERE run_number IS NOT NULL
