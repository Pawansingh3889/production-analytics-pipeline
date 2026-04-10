![CI](https://github.com/Pawansingh3889/production-analytics-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![dbt](https://img.shields.io/badge/dbt-1.11-orange)

# Production Analytics Pipeline

dbt analytics pipeline for fish production data. Models yield, waste, temperature compliance, and shift productivity from ERP transaction data.

## Schema

10 tables modelling a fish processing factory: production runs, pack-level transactions, PLU/product master, traceability (catch-to-pack), temperature monitoring, non-conformance tracking, shift labour, and despatch.

## dbt Models

### Staging
- `stg_runs` -- cleaned production runs with calculated yield
- `stg_temperature` -- temperature readings with breach detection
- `stg_non_conformance` -- quality records with days-to-close

### Marts
- `fct_daily_yield` -- daily yield and waste by line, product, customer
- `fct_temp_breaches` -- HACCP temperature breach summary by location
- `fct_quality_summary` -- NC trends by type, severity, closure rate
- `fct_shift_productivity` -- labour KPIs: kg/head, kg/hour, overtime %

## Interview Queries

10 production SQL scenarios covering:
1. Daily yield by line
2. Full traceability chain (product to vessel)
3. Temperature breach audit report
4. Giveaway/waste analysis
5. Day vs night shift productivity
6. Open critical non-conformances
7. Order fulfilment shortfall detection
8. Allergen changeover detection (LAG window function)
9. Species yield ranking (RANK window function)
10. Cumulative weekly production (running total)

## Stack

SQL Server, dbt, Python, BRC/HACCP compliance patterns
