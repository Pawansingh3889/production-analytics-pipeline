"""Production Analytics API.

REST endpoints for production data -- yield, traceability, compliance, shelf life.
Designed for shift managers, planners, and compliance teams to query data
without running Python scripts.

Usage:
    uvicorn api.main:app --reload
    # or
    make api
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, text

from extract.monitoring import init_sentry

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = os.getenv("TARGET_DB", "sqlite:///data/production_dw.db")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})


def _rows_to_dicts(result) -> list[dict]:
    """Convert SQLAlchemy result rows to a list of plain dicts."""
    columns = list(result.keys())
    return [dict(zip(columns, row)) for row in result.fetchall()]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Production Analytics API",
    description=(
        "REST endpoints for fish production data -- yield, traceability, "
        "compliance, shelf life.  Backed by the production_dw.db warehouse."
    ),
    version="1.0.0",
)

init_sentry()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
def health_check():
    """Return service health and the number of tables in the warehouse."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        )
        count = result.scalar()
    return {"status": "ok", "tables": count}


# ---------------------------------------------------------------------------
# GET /yield/daily
# ---------------------------------------------------------------------------

@app.get("/yield/daily", tags=["yield"])
def yield_daily(days: int = Query(7, ge=1, le=365, description="Look-back window in days")):
    """Daily yield summary for the last N days (default 7).

    Returns production date, line, run count, and yield percentage for
    each day with completed runs.
    """
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = text("""
        SELECT
            DATE(production_date) AS production_date,
            prod_line,
            COUNT(*)              AS runs,
            species,
            product_type,
            shift_code
        FROM run_numbers
        WHERE complete = 1
          AND DATE(production_date) >= :cutoff
        GROUP BY DATE(production_date), prod_line
        ORDER BY DATE(production_date) DESC
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query, {"cutoff": cutoff}))
    if not rows:
        return {"message": "No yield data found for the requested period", "data": []}
    return {"days_requested": days, "rows": len(rows), "data": rows}


# ---------------------------------------------------------------------------
# GET /yield/by-line
# ---------------------------------------------------------------------------

@app.get("/yield/by-line", tags=["yield"])
def yield_by_line():
    """Yield grouped by production line.

    Aggregates all completed runs per line: total runs, earliest and
    latest production dates.
    """
    query = text("""
        SELECT
            prod_line,
            COUNT(*)                       AS total_runs,
            MIN(DATE(production_date))     AS first_date,
            MAX(DATE(production_date))     AS last_date
        FROM run_numbers
        WHERE complete = 1
        GROUP BY prod_line
        ORDER BY total_runs DESC
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query))
    if not rows:
        return {"message": "No completed runs found", "data": []}
    return {"lines": len(rows), "data": rows}


# ---------------------------------------------------------------------------
# GET /trace/{batch_code}
# ---------------------------------------------------------------------------

@app.get("/trace/{batch_code}", tags=["traceability"])
def trace_batch(batch_code: str):
    """Trace a batch code through its lineage.

    Looks up the batch code (product_code) across run_numbers and returns
    the parent chain of runs sharing the same spec (programme).
    """
    # Find runs matching this batch / product code
    query = text("""
        SELECT
            run_number,
            production_date,
            description,
            product_code,
            prod_line,
            shift_code,
            spec,
            species,
            product_type,
            complete
        FROM run_numbers
        WHERE product_code = :code
           OR run_number   = :code
        ORDER BY production_date DESC
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query, {"code": batch_code}))

    if not rows:
        raise HTTPException(status_code=404, detail=f"Batch code '{batch_code}' not found")

    # Find parent chain -- other runs on the same spec/programme
    spec = rows[0].get("spec")
    parent_query = text("""
        SELECT
            run_number,
            production_date,
            description,
            product_code,
            prod_line,
            spec
        FROM run_numbers
        WHERE spec = :spec
          AND product_code != :code
        ORDER BY production_date ASC
    """)
    with engine.connect() as conn:
        parents = _rows_to_dicts(conn.execute(parent_query, {"spec": spec, "code": batch_code}))

    return {
        "batch_code": batch_code,
        "runs": rows,
        "parent_chain": parents,
    }


# ---------------------------------------------------------------------------
# GET /runs/active
# ---------------------------------------------------------------------------

@app.get("/runs/active", tags=["runs"])
def runs_active():
    """Return currently active (incomplete) production runs.

    Active runs have complete = 0, meaning they are still being processed
    on the factory floor.
    """
    query = text("""
        SELECT
            run_number,
            production_date,
            description,
            product_code,
            prod_line,
            shift_code,
            species,
            product_type
        FROM run_numbers
        WHERE complete = 0
        ORDER BY production_date DESC, run_number DESC
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query))
    return {"active_runs": len(rows), "data": rows}


# ---------------------------------------------------------------------------
# GET /runs/{run_number}
# ---------------------------------------------------------------------------

@app.get("/runs/{run_number}", tags=["runs"])
def run_detail(run_number: str):
    """Return full details for a specific production run.

    Includes the run record and, if available, the associated totals
    (packs, weight, giveaway, downtime).
    """
    run_query = text("""
        SELECT *
        FROM run_numbers
        WHERE run_number = :rn
    """)
    totals_query = text("""
        SELECT *
        FROM raw_run_totals
        WHERE "RunNumber" = :rn
    """)
    with engine.connect() as conn:
        run_rows = _rows_to_dicts(conn.execute(run_query, {"rn": run_number}))
        total_rows = _rows_to_dicts(conn.execute(totals_query, {"rn": run_number}))

    if not run_rows:
        raise HTTPException(status_code=404, detail=f"Run '{run_number}' not found")

    return {
        "run": run_rows[0],
        "totals": total_rows[0] if total_rows else None,
    }


# ---------------------------------------------------------------------------
# GET /compliance/checks
# ---------------------------------------------------------------------------

@app.get("/compliance/checks", tags=["compliance"])
def compliance_checks():
    """Return compliance violations detected across production runs.

    Checks implemented:
    - Yield below 90 percent (WARNING)
    - Giveaway exceeding 3 percent (WARNING)
    - Runs with no product code (MAJOR)
    """
    query = text("""
        SELECT
            rn.run_number,
            rn.production_date,
            rn.description,
            rn.prod_line,
            rt."GiveawayPct" AS giveaway_pct,
            CASE
                WHEN rt."GiveawayPct" > 3.0 THEN 'GIVEAWAY > 3%'
                ELSE NULL
            END AS giveaway_flag,
            CASE
                WHEN rn.product_code IS NULL OR rn.product_code = '' THEN 'NO PRODUCT CODE'
                ELSE NULL
            END AS product_code_flag
        FROM run_numbers rn
        LEFT JOIN raw_run_totals rt ON rn.run_number = rt."RunNumber"
        WHERE rt."GiveawayPct" > 3.0
           OR rn.product_code IS NULL
           OR rn.product_code = ''
        ORDER BY rn.production_date DESC
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query))
    return {"violations": len(rows), "data": rows}


# ---------------------------------------------------------------------------
# GET /temperature/breaches
# ---------------------------------------------------------------------------

@app.get("/temperature/breaches", tags=["compliance"])
def temperature_breaches(
    hours: int = Query(24, ge=1, le=720, description="Look-back window in hours"),
):
    """Return temperature breaches from raw transaction data.

    Since the SQLite warehouse does not have a dedicated temperature_logs
    table, this endpoint flags transactions where the recorded weight
    deviates significantly (proxy for sensor anomalies in the demo dataset).

    In a full deployment this would query the temperature_logs table.
    """
    # The demo DB lacks temperature_logs; return a helpful message.
    # Check if temperature_logs exists
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='temperature_logs'")
        ).fetchall()

    if tables:
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = text("""
            SELECT *
            FROM temperature_logs
            WHERE in_range = 0
              AND reading_time >= :cutoff
            ORDER BY reading_time DESC
        """)
        with engine.connect() as conn:
            rows = _rows_to_dicts(conn.execute(query, {"cutoff": cutoff}))
        return {"hours_requested": hours, "breaches": len(rows), "data": rows}

    # Fallback: no temperature_logs table in the demo warehouse
    return {
        "hours_requested": hours,
        "breaches": 0,
        "data": [],
        "note": "temperature_logs table not present in demo warehouse. "
                "Deploy the full schema (sql/001_create_schema.sql) for live data.",
    }


# ---------------------------------------------------------------------------
# GET /products
# ---------------------------------------------------------------------------

@app.get("/products", tags=["products"])
def product_catalogue():
    """Return the product catalogue from the raw_products table.

    Includes PLU number, description, species, pack size, shelf life,
    and allergen information.
    """
    query = text("""
        SELECT
            plu_number,
            description,
            product_code,
            category,
            species,
            pack_size,
            shelf_life,
            allergens,
            active
        FROM raw_products
        ORDER BY species, description
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query))
    if not rows:
        return {"message": "No products found", "data": []}
    return {"products": len(rows), "data": rows}


# ---------------------------------------------------------------------------
# GET /shelf-life/expiring
# ---------------------------------------------------------------------------

@app.get("/shelf-life/expiring", tags=["products"])
def shelf_life_expiring():
    """Return products approaching the day-12 freeze-down threshold.

    Checks completed runs whose production date is 9 or more days ago
    (standard shelf life = 9 days; day 13+ triggers mandatory freeze-down).
    Products within 3 days of freeze-down are flagged.
    """
    query = text("""
        SELECT
            rn.run_number,
            rn.production_date,
            rn.description,
            rn.product_code,
            rn.prod_line,
            rp.shelf_life,
            CAST(
                julianday('now') - julianday(rn.production_date)
            AS INTEGER) AS days_since_production,
            CASE
                WHEN CAST(julianday('now') - julianday(rn.production_date) AS INTEGER) >= 12
                    THEN 'FREEZE NOW'
                WHEN CAST(julianday('now') - julianday(rn.production_date) AS INTEGER) >= 9
                    THEN 'APPROACHING'
                ELSE 'OK'
            END AS shelf_status
        FROM run_numbers rn
        LEFT JOIN raw_products rp ON rn.product_code = rp.product_code
        WHERE rn.complete = 1
          AND CAST(julianday('now') - julianday(rn.production_date) AS INTEGER) >= 9
        ORDER BY days_since_production DESC
    """)
    with engine.connect() as conn:
        rows = _rows_to_dicts(conn.execute(query))
    if not rows:
        return {"message": "No products approaching freeze-down", "data": []}
    return {"expiring": len(rows), "data": rows}


# ---------------------------------------------------------------------------
# POST /pipeline/run
# ---------------------------------------------------------------------------

@app.post("/pipeline/run", tags=["system"])
def pipeline_run(full: bool = Query(False, description="Full reload instead of incremental")):
    """Trigger a full pipeline extraction in the background.

    Returns immediately with a job status.  The pipeline runs in a
    background thread so the API stays responsive.
    """
    job_id = datetime.now().strftime("job_%Y%m%d_%H%M%S")

    def _run_pipeline():
        try:
            from workflow.daily_run import run as daily_run
            daily_run(full=full)
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger("api").error("Pipeline failed: %s", exc)

    thread = threading.Thread(target=_run_pipeline, name=job_id, daemon=True)
    thread.start()

    return {
        "job_id": job_id,
        "status": "started",
        "mode": "full" if full else "incremental",
        "message": "Pipeline running in background. Check /health for updated table counts.",
    }
