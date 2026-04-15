![CI](https://github.com/Pawansingh3889/production-analytics-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![dbt](https://img.shields.io/badge/dbt-1.11-orange)

# Production Analytics Pipeline

## Links
- [GitHub](https://github.com/Pawansingh3889/production-analytics-pipeline)
- [API Docs](http://localhost:8000/docs) (when running)
- [Dashboard](http://localhost:3000) (when running)
- [n8n Workflows](http://localhost:5678) (when running)
- [Profile](https://github.com/Pawansingh3889)

## What Problem Does This Solve?

Shift managers in fish processing factories rely on delayed Excel reports and manual data entry to track production. By the time they see the numbers, the shift is over. This pipeline pulls data automatically from the factory ERP, transforms it, and serves live dashboards — so decisions happen during the shift, not after.

### Key Results

| Metric | Value |
|---|---|
| Daily rows processed | 15,000+ |
| API endpoints | 11 (FastAPI) |
| Automated tests | 53 |
| Data sources | 4 SI Integreater tables |
| Dashboards | Next.js (live) + Power BI (export) |
| Orchestration | Prefect with retry logic |

---

Incremental ETL pipeline for fish production data. Extracts from legacy ERP tables, validates with Pydantic, transforms with dbt. Handles batch-centric production runs (one batch, multiple products), waterfall yield tracking across RSPCA/GG/Almaria tiers, batch lineage for OCM scan-back traceability, shelf life management (0/+1/+2/+3 adjustments), and paperwork digitisation.

## Architecture

```
SI Integreater (ERP)
    |
    v
[Extract] --- extract/incremental.py, Pydantic validation
    |
    v
[Transform] --- dbt staging views + mart tables
    |
    +---> [FastAPI] --- 11 REST endpoints (localhost:8000/docs)
    |
    +---> [Next.js] --- production dashboard (localhost:3000)
    |
    +---> [Power BI] --- CSV export for desktop dashboards
    |
    +---> [Prefect] --- orchestration with retry + monitoring
    |
    +---> [n8n] --- visual workflow automation
    |
    +---> [Sentry] --- error monitoring (opt-in)

Infrastructure: Docker + OpenTofu
Quality: ruff + mypy + pytest (53 tests)
Safety: 6-layer read-only architecture
```

### Extract

Watermark-based incremental load from the ERP database (`extract/incremental.py`). Each run reads only rows where `Updated > last_run_timestamp`, preventing full-table scans on the production ERP. Rows are fetched in configurable batches (default 5 000) to handle `varchar(max)` columns without memory issues. Supports full reload (`--full`) and Parquet output (`--to-parquet`).

### Validate

Pydantic models (`models/run_number.py`) enforce types at the Python boundary. The `RunNumberRecord` model parses species and product type from free-text Description fields using regex pattern matching (12 species, 10 product types). Boolean fields are coerced from the ERP's mixed `int`/`str` representations. Rows that fail validation are written to `data/rejected_rows.csv` for investigation.

### Transform

dbt staging models clean and enrich raw data; mart models aggregate into analysis-ready tables. Three staging views feed four mart tables covering yield, temperature compliance, quality, and labour productivity.

### Serve

10 production SQL queries (`sql/production_queries.sql`) covering daily yield, traceability, temperature audits, giveaway analysis, shift productivity, non-conformance tracking, order fulfilment, allergen changeovers (LAG), species ranking (RANK), and cumulative weekly production (running totals).

## Production Context

### Batch-Centric Runs

One batch feeds one production run, and multiple products come out of that single run (e.g. RSPCA 120g, RSPCA 240g, GG 280g, Family Pack). The batch code ties every output product back to its source material.

Exception products (Family Pack, marinades, Simply Salmon) use separate runs where multiple batch codes are documented on the paperwork. These require explicit batch-to-run mapping during data entry.

### Waterfall Yield

Production follows a three-tier waterfall where raw material cascades downward through quality tiers:

| Tier | Examples | Notes |
|---|---|---|
| Tier 1 (RSPCA) | 120g premium, 240g portions | Highest certification, allocated first |
| Tier 2 (GG) | 140g standard, marinades | Standard tier plus value-added |
| Tier 3 (Almaria / Simply Salmon) | Simply Salmon catch-all | Absorbs remaining material |

**Golden rule:** RSPCA material cascades down to GG or Almaria, but GG material never goes up to RSPCA. Tails are never packed into RSPCA products.

### Shelf Life

| Scenario | Calculation |
|---|---|
| Standard | Pack date + 9 days |
| Rubber clock (+1) | Pack date + 10 days |
| Superchill (+2) | Pack date + 11 days |
| Superchill (+3) | Pack date + 12 days |
| Freeze down | Day 13+ triggers freeze down |

### Paperwork

Production paperwork captured during digitisation includes:

- **Baskets** -- physical container tracking through the line
- **Start/end labels** -- printed from OCM system for scan-back traceability
- **Batch codes with kg per batch** -- weight reconciliation against ERP totals

## Compliance Checks

Automated checks run against every production run:

| Check | Severity | Description |
|---|---|---|
| GG batch in RSPCA product | CRITICAL | GG-certified material must not appear in RSPCA-labelled output |
| Tails in RSPCA product | CRITICAL | Tail cuts are excluded from RSPCA tier products |
| Species mismatch | CRITICAL | Product species must match the batch species declaration |
| OCM scan-back without parent mapping | MAJOR | Every OCM label must trace back to a parent batch code |
| Yield below 90% | WARNING | Flags runs with unusually low yield for investigation |
| Temperature breach | CRITICAL | HACCP temperature reading outside permitted range |
| Giveaway exceeding 3% | WARNING | Pack weight giveaway above target triggers review |
| Label gap detection | WARNING | Missing label sequence numbers indicate potential traceability gaps |

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

## Orchestration

The daily workflow can run standalone (`python -m workflow.daily_run`) or orchestrated via Prefect (`python -m workflow.prefect_flow`). Prefect adds automatic retry logic (2 retries with 30-second delay on each extraction task), a scheduling system for recurring runs, a monitoring dashboard with run history, and structured logging.

To use Prefect orchestration:

```bash
pip install prefect>=3.0

# Run the flow directly
python -m workflow.prefect_flow          # incremental
python -m workflow.prefect_flow --full   # full reload

# Or use Make targets
make prefect-run                         # run flow
make prefect-serve                       # start Prefect UI at http://localhost:4200
```

## Power BI Integration

Export production mart data to CSV files that can be imported into Power BI Desktop for dashboarding and ad-hoc analysis.

### Export CSVs

```bash
make export-powerbi
# or
python -m reports.powerbi_export
```

CSV files are written to `reports/powerbi/`:

| File | Contents |
|---|---|
| `daily_yield.csv` | Production runs aggregated by date, shift, line, species |
| `shift_productivity.csv` | Shift-level output, giveaway, and downtime KPIs |
| `compliance_checks.csv` | Per-run compliance status and giveaway warnings |

If dbt mart tables have been materialised (`fct_daily_yield`, `fct_shift_productivity`, `fct_compliance_checks`), the export uses those directly. Otherwise it falls back to equivalent queries against the raw tables.

### Connect Power BI Desktop

1. Open Power BI Desktop.
2. Click **Get Data** -> **Text/CSV**.
3. Select one or more CSV files from `reports/powerbi/`.
4. Load the data and build your reports.

## REST API

FastAPI service exposing production data over HTTP. Shift managers, planners, and compliance teams can query data without running Python scripts.

### Run

```bash
make api
# or
uvicorn api.main:app --reload
```

Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs).

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service health and table count |
| GET | `/yield/daily` | Daily yield summary (default last 7 days, `?days=N`) |
| GET | `/yield/by-line` | Yield grouped by production line |
| GET | `/trace/{batch_code}` | Trace a batch code through its lineage |
| GET | `/runs/active` | Currently active (incomplete) runs |
| GET | `/runs/{run_number}` | Details for a specific run |
| GET | `/compliance/checks` | Compliance violations (giveaway, missing codes) |
| GET | `/temperature/breaches` | Temperature breaches (default last 24h, `?hours=N`) |
| GET | `/products` | Product catalogue |
| GET | `/shelf-life/expiring` | Products approaching day-12 freeze-down |
| POST | `/pipeline/run` | Trigger pipeline extraction (`?full=true` for full reload) |

## Error Monitoring

Optional Sentry integration for error tracking. Disabled by default (no-op if `SENTRY_DSN` is not set).

To enable, set the `SENTRY_DSN` environment variable:

```bash
export SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
export ENVIRONMENT="production"   # optional, defaults to "development"
```

When enabled, Sentry captures:

- Pipeline failures during daily extraction runs
- API errors in the FastAPI service
- Extraction and validation issues across all source tables

The monitoring module (`extract/monitoring.py`) gracefully degrades -- if `sentry-sdk` is not installed or `SENTRY_DSN` is unset, all monitoring calls are silent no-ops.

## Web Dashboard

Real-time production dashboard built with Next.js 15, Tailwind CSS, and Recharts. Connects to the FastAPI backend (`make api`) and displays yield charts, active runs, temperature breaches, and compliance status.

### Run

```bash
make dashboard-install   # install Node dependencies
make dashboard-dev       # start dev server
```

Opens at [http://localhost:3000](http://localhost:3000). Requires the FastAPI backend running on port 8000.

### Features

- Four KPI cards: Total Yield, Active Runs, Temp Breaches, Compliance Issues
- Daily yield bar chart (Recharts)
- Active runs table with live data
- Auto-refresh every 60 seconds
- Graceful "API unavailable" state when backend is offline
- Dark theme (bg-gray-950)

## Infrastructure as Code

OpenTofu (Terraform-compatible) configuration in `infra/` manages the containerised deployment:

| Resource | Description |
|---|---|
| SQL Server sandbox | `mcr.microsoft.com/mssql/server:2022-latest` on port 1433 |
| FastAPI container | Production API built from `infra/Dockerfile.api` on port 8000 |
| Warehouse volume | Persistent Docker volume for DuckDB/SQLite data |

### Commands

```bash
make infra-init     # initialise OpenTofu providers
make infra-plan     # preview infrastructure changes
make infra-apply    # create/update containers and volumes
make infra-destroy  # tear down all managed resources
```

Requires [OpenTofu](https://opentofu.org/) installed locally. State files and the `.terraform/` directory are excluded from version control via `infra/.gitignore`.

## Visual Workflows

n8n provides a visual workflow editor for non-technical users (shift managers, planners, QA leads) to build automation on top of the FastAPI endpoints without writing code.

### Run

```bash
make n8n-start    # start n8n container
```

Open [http://localhost:5678](http://localhost:5678) (admin / production2026). Requires the FastAPI backend running on port 8000.

### Suggested Workflows

| Workflow | Schedule | What It Does |
|---|---|---|
| Daily Data Extraction | Every day at 06:00 | POST /pipeline/run, wait, check /health, notify |
| Temperature Alert | Every 15 minutes | GET /temperature/breaches, alert if any found |
| Compliance Check | Every hour | GET /compliance/checks, filter critical, alert |
| Weekly Yield Report | Every Monday 08:00 | GET /yield/daily?days=7, format HTML table, email |
| Shelf Life Monitor | Every 4 hours | GET /shelf-life/expiring, alert if approaching day 12 |

All workflows connect to the FastAPI backend (`http://localhost:8000`). Build them visually in the n8n drag-and-drop editor.

## Stack

| Component | Technology |
|---|---|
| Database | SQL Server (ERP source), SQLite (local dev) |
| ORM / connectivity | SQLAlchemy |
| Schema validation | Pydantic |
| Transformation | dbt |
| Orchestration | Prefect 3 |
| API | FastAPI + Uvicorn |
| Visual workflows | n8n |
| Infrastructure | OpenTofu (Terraform-compatible) |
| Testing | pytest |
| Error monitoring | Sentry (opt-in via `SENTRY_DSN`) |
| Dashboard | Next.js 15 + Tailwind CSS + Recharts |
| Language | Python 3.11+ |
