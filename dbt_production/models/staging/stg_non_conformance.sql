-- Staging: quality non-conformance records
SELECT
    nc_id,
    nc_date,
    run_number,
    product_code,
    LOWER(TRIM(nc_type)) AS nc_type,
    LOWER(TRIM(severity)) AS severity,
    description,
    root_cause,
    corrective_action,
    raised_by,
    closed_by,
    closed_date,
    LOWER(TRIM(status)) AS status,
    CASE
        WHEN closed_date IS NOT NULL THEN closed_date - nc_date
        ELSE NULL
    END AS days_to_close
FROM {{ source('production', 'non_conformance') }}
