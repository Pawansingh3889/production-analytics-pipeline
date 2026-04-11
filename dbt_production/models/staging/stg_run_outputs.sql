-- Staging: run outputs with tier and grade validation
SELECT
    o.output_id,
    o.run_number,
    o.product_code,
    p.description AS product_name,
    p.brand,
    o.tier,
    o.piece_type,
    o.qty_packs,
    o.qty_kg,
    o.source_grade,
    p.species,
    -- Compliance check: does grade allow this tier?
    CASE
        WHEN o.source_grade = 'GG' AND o.tier = 1 THEN 0
        WHEN o.piece_type = 'tail' AND o.tier = 1 THEN 0
        ELSE 1
    END AS compliant
FROM {{ source('production', 'run_outputs') }} o
LEFT JOIN {{ source('production', 'product_catalogue') }} p
    ON o.product_code = p.product_code
