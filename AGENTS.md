# AGENTS.md

Context for AI assistants working on this codebase.

## Purpose

Incremental ETL pipeline that extracts fish production data from a legacy SQL Server ERP system (RunNumber tables), validates it with Pydantic, transforms it with dbt, and serves it via SQL queries and dashboards. The pipeline is designed for a fish processing factory and handles species parsing, yield tracking, temperature compliance, quality records, and labour productivity.

## Architecture

```
ERP (SQL Server) -> Extract (watermark-based) -> Validate (Pydantic) -> Clean -> Load (Parquet / DB)
                                                                              -> dbt staging -> mart tables
```

1. **Extract** -- Watermark-based incremental load. Reads only rows where `Updated > last_run_timestamp`. Batches of 5,000 rows. Supports full reload (`--full`) and Parquet output (`--to-parquet`).
2. **Validate** -- Pydantic models parse and enforce types. Species and product type are extracted from free-text Description fields via regex. Invalid rows go to `data/rejected_rows.csv`.
3. **Clean** -- Column renaming and type coercion (booleans from mixed int/str ERP representations).
4. **Load** -- Upsert to target database or write Parquet files. Pipeline state (watermark) persisted in `data/pipeline_state.json`.
5. **Transform** -- dbt staging views clean raw data; mart tables aggregate into analysis-ready outputs.

## Key Files

| File | Role |
|---|---|
| `workflow/daily_run.py` | Orchestrator -- runs the full daily ETL pipeline |
| `extract/extractor.py` | Query builder, batch fetcher, SQL safety guards |
| `extract/incremental.py` | Incremental load entry point (watermark logic) |
| `extract/cleaner.py` | Column renaming and data cleaning |
| `extract/loader.py` | Database upsert and Parquet writer |
| `extract/config.py` | Environment-based configuration, SA credential blocking |
| `models/run_number.py` | Pydantic model (`RunNumberRecord`) with species/product parsing |
| `extract/sources/run_number.py` | RunNumber source table definition |
| `extract/sources/transactions.py` | SI_OCM_TRANS source table definition |
| `extract/sources/plu.py` | SI_OCM_PLU source table definition |
| `extract/sources/totals.py` | SI_OCM_TOTALS source table definition |
| `workflow/prefect_flow.py` | Prefect-orchestrated flow with retry logic |
| `api/main.py` | FastAPI REST API -- 11 endpoints for production data |
| `extract/monitoring.py` | Sentry error monitoring (opt-in via `SENTRY_DSN` env var) |

## Source Tables

Four ERP source tables are extracted:

| Source Table | Source File |
|---|---|
| `RunNumber` | `extract/sources/run_number.py` |
| `SI_OCM_TRANS` | `extract/sources/transactions.py` |
| `SI_OCM_PLU` | `extract/sources/plu.py` |
| `SI_OCM_TOTALS` | `extract/sources/totals.py` |

## dbt Models

Located in `dbt_production/models/`. Project config in `dbt_production/dbt_project.yml`.

### Staging (3 views)

- `stg_runs` -- Cleaned production runs with calculated yield percentage
- `stg_temperature` -- Temperature readings with breach detection flags
- `stg_non_conformance` -- Quality records with days-to-close calculation

### Marts (4 tables)

- `fct_daily_yield` -- Daily yield and waste by line, product, customer
- `fct_temp_breaches` -- HACCP temperature breach summary by location
- `fct_quality_summary` -- Non-conformance trends by type, severity, closure rate
- `fct_shift_productivity` -- Labour KPIs (kg/head, kg/hour, overtime percentage)

## Docker Sandbox

- `docker-compose.yml` -- SQL Server container isolated from the real ERP
- `scripts/setup_sandbox.py` -- Bootstrap script (refuses non-localhost targets)
- `scripts/init_sandbox.sql` -- Creates a read-only database user

## Tests

53 tests across three files. Run with:

```
python -m pytest tests/ -v
```

Test areas:
- `tests/test_models.py` -- Pydantic validation, species parsing (9 species), product type parsing (11 types), boolean coercion, description uppercasing
- `tests/test_extraction.py` -- Query building (full vs incremental), state persistence, row validation (valid/invalid/mixed batches)
- `tests/test_safety.py` -- SELECT * blocking, SQL injection prevention, write keyword detection, SA credential rejection

## Safety Rules

These are non-negotiable. Every change must preserve all six safety layers:

1. **No SELECT *** -- All queries must list explicit columns. The query validator in `extract/extractor.py` blocks `SELECT *`.
2. **No SA credentials** -- `extract/config.py` rejects connection strings containing SA or admin credentials.
3. **Read-only queries** -- The query validator blocks write keywords: DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, EXEC, xp_, sp_.
4. **SQL injection guards** -- `extract/extractor.py` blocks semicolons, comment sequences (`--`, `/*`), and `xp_cmdshell`.
5. **Docker isolation** -- The sandbox container is separate from the production ERP.
6. **Read-only DB user** -- The sandbox user has DENY on INSERT, UPDATE, DELETE, ALTER.

When modifying `extract/extractor.py`, always run `tests/test_safety.py` to confirm guards are intact.

## Conventions

- **Clean columns**: `snake_case` (e.g., `run_number`, `species_code`)
- **ERP source columns**: `PascalCase` preserved as-is from the ERP (e.g., `RunNumber`, `Description`, `Updated`)
- **Schema enforcement**: All data passes through Pydantic models before loading. Add or modify models in `models/run_number.py`.
- **Environment config**: `SOURCE_DB`, `TARGET_DB`, `STATE_FILE` environment variables. Defaults point to local SQLite for development.
- **Batch size**: 5,000 rows default, configurable.
- **Rejected rows**: Written to `data/rejected_rows.csv` for manual investigation.

## Orchestration

`workflow/prefect_flow.py` wraps the daily pipeline with Prefect tasks and flows. Each extraction step (run numbers, transactions, PLU, totals) is a `@task` with `retries=2, retry_delay_seconds=30`. The main `daily_production_flow` is a `@flow` that runs all four extraction tasks, validates results, and prints a summary. Supports `--full` flag for full reload. Prefect provides a monitoring dashboard (`prefect server start`) with run history and failure alerts.

## Power BI Export

`reports/powerbi_export.py` exports mart-level data (daily yield, shift productivity, compliance checks) to CSV files in `reports/powerbi/`. If dbt mart tables exist they are used directly; otherwise fallback queries run against raw tables. Run with `make export-powerbi` or `python -m reports.powerbi_export`.

## REST API

`api/main.py` is a FastAPI application serving 11 endpoints over HTTP. It queries `data/production_dw.db` via SQLAlchemy (read-only). Start with `make api` or `uvicorn api.main:app --reload`. Swagger docs at `http://localhost:8000/docs`.

Endpoints: `/health`, `/yield/daily`, `/yield/by-line`, `/trace/{batch_code}`, `/runs/active`, `/runs/{run_number}`, `/compliance/checks`, `/temperature/breaches`, `/products`, `/shelf-life/expiring`, `POST /pipeline/run`.

The `POST /pipeline/run` endpoint triggers the daily workflow in a background thread. All GET endpoints return JSON with graceful empty-result handling.

## Error Monitoring

`extract/monitoring.py` provides optional Sentry integration. Set `SENTRY_DSN` environment variable to enable; if unset, all monitoring calls are silent no-ops. The module is imported in `workflow/daily_run.py`, `workflow/prefect_flow.py`, and `api/main.py`. It captures pipeline failures, API errors, and extraction issues. Traces sample rate is 0.1. The `ENVIRONMENT` env var controls the Sentry environment tag (defaults to `development`).

## Running the Pipeline

```bash
# Incremental load (default)
python -m extract.incremental

# Full reload
python -m extract.incremental --full

# Output to Parquet
python -m extract.incremental --to-parquet

# Daily orchestration
python workflow/daily_run.py

# Prefect-orchestrated flow
python -m workflow.prefect_flow
python -m workflow.prefect_flow --full

# Run tests
python -m pytest tests/ -v
```
