-- Mart: shift-level productivity KPIs
-- Used for labour planning and efficiency tracking

SELECT
    s.shift_date,
    s.shift_code,
    l.line_name,
    l.line_type,
    s.headcount,
    s.planned_hours,
    s.actual_hours,
    s.overtime_hours,
    s.output_kg,
    ROUND(s.output_kg / NULLIF(s.headcount, 0), 1) AS kg_per_head,
    ROUND(s.output_kg / NULLIF(s.actual_hours, 0), 1) AS kg_per_hour,
    ROUND(s.overtime_hours / NULLIF(s.actual_hours, 0) * 100, 1) AS overtime_pct,
    ROUND(s.actual_hours / NULLIF(s.planned_hours, 0) * 100, 1) AS hours_utilisation_pct
FROM {{ source('production', 'shifts') }} s
LEFT JOIN {{ source('production', 'prod_lines') }} l
    ON s.line_id = l.line_id
