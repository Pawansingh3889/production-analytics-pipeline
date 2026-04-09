-- Mart: temperature breach summary for HACCP compliance
-- Critical for BRC audits — shows breach frequency and severity

SELECT
    t.reading_date,
    t.location,
    COUNT(*) AS total_readings,
    SUM(t.is_breach) AS breach_count,
    ROUND(
        SUM(t.is_breach) * 100.0 / COUNT(*), 1
    ) AS breach_pct,
    MIN(t.temp_celsius) AS min_temp,
    MAX(t.temp_celsius) AS max_temp,
    ROUND(AVG(t.temp_celsius), 1) AS avg_temp,
    MIN(t.target_min) AS target_min,
    MAX(t.target_max) AS target_max,
    MAX(CASE WHEN t.is_breach = 1 THEN t.temp_celsius END) AS worst_breach_temp
FROM {{ ref('stg_temperature') }} t
GROUP BY t.reading_date, t.location
