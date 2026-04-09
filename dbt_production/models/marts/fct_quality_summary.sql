-- Mart: non-conformance summary for quality KPI tracking
-- Shows NC trends by type, severity, and closure rate

SELECT
    nc.nc_date,
    nc.nc_type,
    nc.severity,
    COUNT(*) AS nc_count,
    SUM(CASE WHEN nc.status = 'closed' THEN 1 ELSE 0 END) AS closed_count,
    SUM(CASE WHEN nc.status = 'open' THEN 1 ELSE 0 END) AS open_count,
    SUM(CASE WHEN nc.status = 'investigating' THEN 1 ELSE 0 END) AS investigating_count,
    ROUND(
        SUM(CASE WHEN nc.status = 'closed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
    ) AS closure_rate_pct,
    ROUND(AVG(nc.days_to_close), 1) AS avg_days_to_close
FROM {{ ref('stg_non_conformance') }} nc
GROUP BY nc.nc_date, nc.nc_type, nc.severity
