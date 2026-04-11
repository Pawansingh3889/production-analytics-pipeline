-- Mart: compliance violations — catches grade/tier mismatches
-- Critical for BRC audits and customer compliance

SELECT
    o.run_number,
    r.production_date,
    o.product_code,
    o.product_name,
    o.brand,
    o.tier,
    o.source_grade,
    o.piece_type,
    o.qty_kg,
    CASE
        WHEN o.source_grade = 'GG' AND o.tier = 1
        THEN 'CRITICAL: GG material in RSPCA product'
        WHEN o.piece_type = 'tail' AND o.tier = 1
        THEN 'CRITICAL: Tail pieces in RSPCA product'
        WHEN o.source_grade = 'RSPCA' AND o.brand = 'GG' AND o.piece_type = 'center_cut'
        THEN 'INFO: RSPCA downgraded to GG (value loss)'
        ELSE 'OK'
    END AS compliance_status,
    CASE
        WHEN o.source_grade = 'GG' AND o.tier = 1 THEN 'CRITICAL'
        WHEN o.piece_type = 'tail' AND o.tier = 1 THEN 'CRITICAL'
        ELSE 'OK'
    END AS severity
FROM {{ ref('stg_run_outputs') }} o
LEFT JOIN {{ ref('stg_runs') }} r ON o.run_number = r.run_number
WHERE o.compliant = 0
   OR (o.source_grade = 'RSPCA' AND o.brand = 'GG' AND o.piece_type = 'center_cut')
