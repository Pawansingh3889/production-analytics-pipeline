![CI](https://github.com/Pawansingh3889/production-analytics-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![dbt](https://img.shields.io/badge/dbt-1.11-orange)

# Production Analytics Pipeline

Incremental ETL pipeline for fish production ERP data. Extracts from legacy SQL Server RunNumber tables, validates with Pydantic, transforms with dbt, serves via SQL queries.

## Architecture

```
ERP (SQL Server)        Python              dbt                 Analyst
 RunNumber table  -->  extract/   -->  staging views  -->  production queries
                       incremental.py   mart tables         + dashboards

docker-compose.yml          # SQL Server sandbox container
scripts/init_sandbox.sql    # Read-only user setup
scripts/setup_sandbox.py    # Sandbox bootstrap script
```

### Extract

Watermark-based incremental load from the ERP database (`extract/incremental.py`). Each run reads only rows where `Updated > last_run_timestamp`, preventing full-table scans on the production ERP. Rows are fetched in configurable batches (default 5 000) to handle `varchar(max)` columns without memory issues. Supports full reload (`--full`) and Parquet output (`--to-parquet`).

### Validate

Pydantic models (`models/run_number.py`) enforce types at the Python boundary. The `RunNumberRecord` model parses species and product type from free-text Description fields using regex pattern matching (12 species, 10 product types). Boolean fields are coerced from the ERP's mixed `int`/`str` representations. Rows that fail validation are written to `data/rejected_rows.csv` for investigation.

### Transform

dbt staging models clean and enrich raw data; mart models aggregate into analysis-ready tables. Three staging views feed four mart tables covering yield, temperature compliance, quality, and labour productivity.

### Serve

10 production SQL queries (`sql/production_queries.sql`) covering daily yield, traceability, temperature audits, giveaway analysis, shift productivity, non-conformance tracking, order fulfilment, allergen changeovers (LAG), species ranking (RANK), and cumulative weekly production (running totals).

## Schema

The schema (`sql/001_create_schema.sql`) models a fish processing factory across 11 tables:

| Table | Purpose |
|---|---|
| `prod_lines` | Production lines with type, area, and capacity |
| `products` | PLU master: species, customer, pack size, allergens, hazard class |
| `runs` | Production runs with target/actual quantities and yield |
| `transactions` | Per-pack weights from inline scales (giveaway calculation) |
| `run_totals` | Shift/run aggregates: packs, weight stats, giveaway, downtime |
| `traceability` | Catch-to-pack chain: supplier, vessel, catch area, certifications |
| `temperature_logs` | HACCP temperature readings with breach detection |
| `non_conformance` | Quality records: type, severity, root cause, corrective actions |
| `case_verification` | Inline scanner verification (expected vs scanned PLU) |
| `despatch` | Customer orders: cases, kg, delivery dates, vehicle temperatures |
| `shifts` | Labour records: headcount, planned/actual hours, kg per head |

## dbt Models

### Staging

| Model | Description |
|---|---|
| `stg_runs` | Cleaned production runs with calculated yield percentage |
| `stg_temperature` | Temperature readings with breach detection flags |
| `stg_non_conformance` | Quality records with days-to-close calculation |

### Marts

| Model | Description |
|---|---|
| `fct_daily_yield` | Daily yield and waste aggregated by line, product, customer |
| `fct_temp_breaches` | HACCP temperature breach summary by location |
| `fct_quality_summary` | Non-conformance trends by type, severity, closure rate |
| `fct_shift_productivity` | Labour KPIs: kg/head, kg/hour, overtime percentage |

## Extraction Pipeline

The pipeline follows an extract-validate-load pattern:

1. **Read watermark** -- Load `data/pipeline_state.json` to get the last successful `Updated` timestamp.
2. **Build query** -- `SELECT <explicit columns> FROM RunNumber WHERE Updated > '<watermark>' ORDER BY Updated ASC`. Never uses `SELECT *`.
3. **Batch fetch** -- Reads rows in batches of 5 000 via SQLAlchemy to control memory usage.
4. **Pydantic validation** -- Each row is parsed through `RunNumberRecord`. Species and product type are extracted from the Description field. Invalid rows are split into a rejected set.
5. **Load** -- Valid rows are upserted to the target database (or saved as Parquet).
6. **Update state** -- The maximum `Updated` value becomes the next watermark.

```
python -m extract.incremental              # incremental (default)
python -m extract.incremental --full        # full reload
python -m extract.incremental --to-parquet  # save to parquet
```

Configuration is via environment variables (`SOURCE_DB`, `TARGET_DB`, `STATE_FILE`). Defaults point to local SQLite databases for development.

## Safety

6 layers of protection prevent accidental writes to the source ERP:

| Layer | Protection | File |
|---|---|---|
| Config guard | Blocks SA/admin credentials in SOURCE_DB | `extract/config.py` |
| Query validator | Blocks SELECT *, SQL injection, write keywords (DROP/DELETE/INSERT/UPDATE/ALTER/TRUNCATE/EXEC/xp_/sp_) | `extract/extractor.py` |
| Pydantic models | Rejects bad data types and empty primary keys | `models/run_number.py` |
| Docker sandbox | Isolates SQL Server container from real ERP | `docker-compose.yml` |
| Read-only user | DENY INSERT/UPDATE/DELETE/ALTER at database level | `scripts/init_sandbox.sql` |
| Setup script | Refuses to run against non-localhost targets | `scripts/setup_sandbox.py` |

## Tests

53 tests covering four areas:

- **Pydantic models** -- Valid record creation, empty run number rejection, description uppercasing, boolean coercion from int and string, optional field defaults, smoked/breaded product type priority.
- **Species parsing** -- Parametrised tests across 9 species (hake, salmon, cod, haddock, mackerel, tuna, plaice, pollock, unknown).
- **Product type parsing** -- Parametrised tests across 11 product types (fillet, loin, portion, steak, smoked, breaded, battered, fish cake, goujon, whole, unknown).
- **Extraction pipeline** -- Query building (full reload vs incremental), state persistence (save/load), row validation (valid pass, invalid rejected, mixed batches).
- **Safety guards** -- SELECT * blocking, SQL injection prevention (semicolons, comments, xp_cmdshell), write keyword detection with whole-word matching (UPDATE vs Updated), SA credential rejection.

```
pytest -v
```

## Stack

| Component | Technology |
|---|---|
| Database | SQL Server (ERP source), SQLite (local dev) |
| ORM / connectivity | SQLAlchemy |
| Schema validation | Pydantic |
| Transformation | dbt |
| Testing | pytest |
| Language | Python 3.11+ |
