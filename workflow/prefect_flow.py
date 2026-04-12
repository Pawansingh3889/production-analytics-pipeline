"""Prefect-orchestrated daily production data workflow.

Wraps the existing daily_run.py pipeline with Prefect tasks and flows,
adding retry logic, observability, and a monitoring dashboard.

Usage:
    python -m workflow.prefect_flow              # incremental (default)
    python -m workflow.prefect_flow --full        # full reload all tables

Serve locally (creates a Prefect deployment):
    prefect server start   # in another terminal
    python -m workflow.prefect_flow --serve
"""
from __future__ import annotations

import sys
from datetime import datetime

from prefect import flow, task, get_run_logger

from extract.extractor import extract_table, get_watermark, set_watermark
from extract.cleaner import clean_run_numbers, clean_transactions, clean_products
from extract.loader import load_to_parquet, load_to_db, load_rejected
from extract.sources import run_number, transactions, plu, totals


# ---------------------------------------------------------------------------
# Tasks -- each extraction step is a discrete, retryable unit of work
# ---------------------------------------------------------------------------

@task(retries=2, retry_delay_seconds=30, name="extract_run_numbers")
def extract_run_numbers(full: bool = False):
    """Extract and load production run numbers from ERP."""
    logger = get_run_logger()
    return _extract_and_load(run_number, cleaner=clean_run_numbers,
                             full=full, logger=logger)


@task(retries=2, retry_delay_seconds=30, name="extract_transactions")
def extract_transactions_task(full: bool = False):
    """Extract and load per-pack weight transactions."""
    logger = get_run_logger()
    return _extract_and_load(transactions,
                             cleaner=lambda df: (clean_transactions(df), None),
                             full=full, logger=logger)


@task(retries=2, retry_delay_seconds=30, name="extract_plu")
def extract_plu(full: bool = False):
    """Extract and load PLU product master."""
    logger = get_run_logger()
    return _extract_and_load(plu,
                             cleaner=lambda df: (clean_products(df), None),
                             full=full, logger=logger)


@task(retries=2, retry_delay_seconds=30, name="extract_totals")
def extract_totals(full: bool = False):
    """Extract and load run totals."""
    logger = get_run_logger()
    return _extract_and_load(totals, full=full, logger=logger)


@task(name="validate_results")
def validate_results(results: list[dict]) -> list[dict]:
    """Log validation summary and flag any tables with rejected rows."""
    logger = get_run_logger()
    for r in results:
        if r["rejected"] > 0:
            logger.warning(
                "%s: %d rows rejected out of %d extracted",
                r["table"], r["rejected"], r["extracted"],
            )
        else:
            logger.info("%s: %d rows OK", r["table"], r["extracted"])
    return results


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------

@flow(name="daily_production_flow", log_prints=True)
def daily_production_flow(full: bool = False):
    """Run the full daily production ETL pipeline.

    Args:
        full: If True, perform a full reload instead of incremental.
    """
    logger = get_run_logger()
    start = datetime.now()

    mode = "FULL RELOAD" if full else "INCREMENTAL"
    logger.info("=" * 60)
    logger.info("DAILY PRODUCTION FLOW (Prefect)")
    logger.info("Mode: %s", mode)
    logger.info("=" * 60)

    # Step 1-4: Extract each source table (retries handled by Prefect)
    r1 = extract_run_numbers(full=full)
    r2 = extract_transactions_task(full=full)
    r3 = extract_plu(full=full)
    r4 = extract_totals(full=full)

    results = [r1, r2, r3, r4]

    # Step 5: Validate
    validated = validate_results(results)

    # Step 6: Summary
    elapsed = (datetime.now() - start).total_seconds()
    total_extracted = sum(r["extracted"] for r in validated)
    total_rejected = sum(r["rejected"] for r in validated)

    logger.info("=" * 60)
    logger.info("WORKFLOW COMPLETE")
    logger.info("Duration: %.1fs", elapsed)
    logger.info("-" * 60)
    for r in validated:
        status = "OK" if r["rejected"] == 0 else f"WARN ({r['rejected']} rejected)"
        logger.info("  %-25s | %6d rows | %s", r["table"], r["extracted"], status)
    logger.info("-" * 60)
    logger.info("  %-25s | %6d rows | %d rejected", "TOTAL", total_extracted, total_rejected)
    logger.info("=" * 60)

    return validated


# ---------------------------------------------------------------------------
# Helpers (shared logic extracted from daily_run.py)
# ---------------------------------------------------------------------------

def _extract_and_load(source, cleaner=None, full=False, logger=None):
    """Extract a single source table, clean, and load.

    Mirrors the logic in daily_run.extract_and_load but uses the Prefect
    logger instead of the stdlib one.
    """
    table = source.TABLE
    columns = source.COLUMNS
    watermark_col = source.WATERMARK_COLUMN
    target = source.TARGET_TABLE

    wm = None if full else get_watermark(table)
    logger.info("Extracting %s (watermark: %s)", table, wm or "FULL")

    df = extract_table(table, columns, watermark_col, wm)

    if df.empty:
        logger.info("  %s: no new rows", table)
        return {"table": table, "extracted": 0, "valid": 0, "rejected": 0}

    logger.info("  %s: %d rows extracted", table, len(df))

    # Clean / validate
    rejected_df = None
    if cleaner:
        df, rejected_df = cleaner(df)
        if rejected_df is not None and not rejected_df.empty:
            load_rejected(rejected_df, target)

    # Load
    mode = "replace" if full else "replace"
    load_to_db(df, target, if_exists=mode)

    # Update watermark
    if not df.empty and watermark_col in [c.lower() for c in df.columns]:
        wm_col = [c for c in df.columns if c.lower() == watermark_col.lower()]
        if wm_col:
            max_wm = str(df[wm_col[0]].max())
            set_watermark(table, max_wm)

    return {
        "table": table,
        "extracted": len(df),
        "valid": len(df),
        "rejected": len(rejected_df) if rejected_df is not None else 0,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    full = "--full" in sys.argv
    daily_production_flow(full=full)
