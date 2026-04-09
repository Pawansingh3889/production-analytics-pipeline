-- Staging: temperature monitoring with breach detection
SELECT
    log_id,
    LOWER(TRIM(location)) AS location,
    reading_time,
    CAST(reading_time AS DATE) AS reading_date,
    temp_celsius,
    target_min,
    target_max,
    CASE
        WHEN temp_celsius < target_min OR temp_celsius > target_max THEN 0
        ELSE 1
    END AS in_range,
    CASE
        WHEN temp_celsius < target_min OR temp_celsius > target_max THEN 1
        ELSE 0
    END AS is_breach,
    recorded_by
FROM {{ source('production', 'temperature_logs') }}
