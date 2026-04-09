-- ============================================================
-- Interview-Ready SQL Queries: Fish Production Analytics
-- Based on real SI Integreater ERP patterns
-- ============================================================


-- Q1: Daily yield by production line (most common production KPI)
-- "Show me yesterday's yield for each line"
SELECT
    r.production_date,
    pl.line_name,
    COUNT(*) AS runs,
    SUM(r.target_qty_kg) AS target_kg,
    SUM(r.actual_qty_kg) AS actual_kg,
    SUM(r.waste_kg) AS waste_kg,
    ROUND(SUM(r.actual_qty_kg) / NULLIF(SUM(r.target_qty_kg), 0) * 100, 1) AS yield_pct
FROM production.runs r
JOIN production.prod_lines pl ON r.prod_line = pl.line_id
WHERE r.status = 'complete'
GROUP BY r.production_date, pl.line_name
ORDER BY r.production_date DESC, yield_pct ASC;


-- Q2: Traceability chain — trace a product back to catch vessel
-- "Customer complaint on batch BC-COD-8831. Where did the fish come from?"
SELECT
    r.run_number,
    r.production_date,
    p.description AS product,
    p.customer,
    t.batch_code,
    t.supplier,
    t.species,
    t.catch_area,
    t.catch_method,
    t.vessel_name,
    t.landing_date,
    t.country_origin,
    t.certified
FROM production.runs r
JOIN production.products p ON r.product_code = p.product_code
JOIN production.traceability t ON r.trace_id = t.trace_id
WHERE t.batch_code = 'BC-COD-8831';


-- Q3: Temperature breach report for BRC audit
-- "Show all temperature breaches this week with corrective actions"
SELECT
    tl.reading_time,
    tl.location,
    tl.temp_celsius,
    tl.target_max,
    tl.temp_celsius - tl.target_max AS degrees_over,
    tl.recorded_by,
    nc.description AS nc_raised,
    nc.corrective_action
FROM production.temperature_logs tl
LEFT JOIN production.non_conformance nc
    ON CAST(tl.reading_time AS DATE) = nc.nc_date
    AND nc.nc_type = 'temp'
WHERE tl.in_range = 0
ORDER BY tl.reading_time;


-- Q4: Giveaway analysis — how much product are we giving away free?
-- "Which products have the highest giveaway percentage?"
SELECT
    p.description,
    p.customer,
    p.pack_size_g,
    COUNT(*) AS total_runs,
    SUM(r.actual_qty_kg) AS total_produced_kg,
    SUM(r.waste_kg) AS total_waste_kg,
    ROUND(SUM(r.waste_kg) / NULLIF(SUM(r.actual_qty_kg), 0) * 100, 2) AS waste_pct,
    ROUND(AVG(r.yield_pct), 1) AS avg_yield
FROM production.runs r
JOIN production.products p ON r.product_code = p.product_code
WHERE r.status = 'complete'
GROUP BY p.description, p.customer, p.pack_size_g
ORDER BY waste_pct DESC;


-- Q5: Shift productivity comparison
-- "Compare day vs night shift efficiency"
SELECT
    s.shift_code,
    COUNT(*) AS total_shifts,
    ROUND(AVG(s.headcount), 0) AS avg_headcount,
    ROUND(AVG(s.output_kg), 0) AS avg_output_kg,
    ROUND(AVG(s.kg_per_head), 1) AS avg_kg_per_head,
    ROUND(AVG(s.overtime_hours), 1) AS avg_overtime_hrs,
    ROUND(SUM(s.output_kg) / NULLIF(SUM(s.actual_hours), 0), 1) AS overall_kg_per_hour
FROM production.shifts s
GROUP BY s.shift_code;


-- Q6: Non-conformance trends — critical NC open > 48 hours
-- "Show me any critical NCs that haven't been closed"
SELECT
    nc.nc_id,
    nc.nc_date,
    nc.nc_type,
    nc.severity,
    nc.description,
    nc.raised_by,
    nc.status,
    DATEDIFF(DAY, nc.nc_date, GETDATE()) AS days_open
FROM production.non_conformance nc
WHERE nc.severity = 'critical'
    AND nc.status != 'closed'
ORDER BY nc.nc_date;


-- Q7: Customer order fulfilment — which orders are at risk?
-- "Are we going to hit Lidl's order for cod fillets?"
SELECT
    d.customer,
    p.description,
    d.qty_cases AS ordered_cases,
    d.qty_kg AS ordered_kg,
    COALESCE(SUM(r.actual_qty_kg), 0) AS produced_kg,
    d.qty_kg - COALESCE(SUM(r.actual_qty_kg), 0) AS shortfall_kg,
    d.delivery_date,
    d.status
FROM production.despatch d
JOIN production.products p ON d.product_code = p.product_code
LEFT JOIN production.runs r
    ON r.product_code = d.product_code
    AND r.production_date = d.despatch_date
    AND r.status = 'complete'
GROUP BY d.customer, p.description, d.qty_cases, d.qty_kg, d.delivery_date, d.status
HAVING d.qty_kg > COALESCE(SUM(r.actual_qty_kg), 0);


-- Q8: Allergen cross-reference check
-- "Which products on Line 3 today contain wheat? Do we need a line clear?"
SELECT
    r.run_number,
    r.production_date,
    pl.line_name,
    p.description,
    p.allergens,
    LAG(p.allergens) OVER (
        PARTITION BY r.prod_line
        ORDER BY r.created_date
    ) AS previous_run_allergens,
    CASE
        WHEN p.allergens != LAG(p.allergens) OVER (
            PARTITION BY r.prod_line ORDER BY r.created_date
        ) THEN 'LINE CLEAR REQUIRED'
        ELSE 'OK'
    END AS allergen_changeover
FROM production.runs r
JOIN production.products p ON r.product_code = p.product_code
JOIN production.prod_lines pl ON r.prod_line = pl.line_id
ORDER BY r.prod_line, r.created_date;


-- Q9: Species yield comparison (window function)
-- "Rank products by yield within each species"
SELECT
    p.species,
    p.description,
    p.customer,
    ROUND(AVG(r.yield_pct), 1) AS avg_yield,
    RANK() OVER (
        PARTITION BY p.species
        ORDER BY AVG(r.yield_pct) DESC
    ) AS yield_rank
FROM production.runs r
JOIN production.products p ON r.product_code = p.product_code
WHERE r.status = 'complete'
GROUP BY p.species, p.description, p.customer;


-- Q10: Running total of daily production (cumulative)
-- "Show cumulative output for the week"
SELECT
    production_date,
    SUM(actual_qty_kg) AS daily_output_kg,
    SUM(SUM(actual_qty_kg)) OVER (
        ORDER BY production_date
        ROWS UNBOUNDED PRECEDING
    ) AS cumulative_kg,
    SUM(waste_kg) AS daily_waste_kg,
    ROUND(
        SUM(waste_kg) / NULLIF(SUM(actual_qty_kg), 0) * 100, 1
    ) AS daily_waste_pct
FROM production.runs
WHERE status = 'complete'
GROUP BY production_date
ORDER BY production_date;
