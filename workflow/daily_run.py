"""Daily production data workflow.

Orchestrates the full pipeline: extract -> validate -> clean -> load -> report.

Usage:
    python -m workflow.daily_run                 # incremental (default)
    python -m workflow.daily_run --full           # full reload all tables
    python -m workflow.daily_run --parquet        # save to parquet instead of DB
    python -m workflow.daily_run --report-only    # skip extraction, just generate reports

Schedule with cron (Linux) or Task Scheduler (Windows):
    # Daily at 6am before shift starts
    0 6 * * * cd /path/to/project && python -m workflow.daily_run
"""
from __future__ import annotations

import sys
import logging
from datetime import datetime

from extract.extractor import extract_table, get_watermark, set_watermark
from extract.cleaner import clean_run_numbers, clean_transactions, clean_products
from extract.loader import load_to_parquet, load_to_db, load_rejected
from extract.sources import run_number, transactions, plu, totals
from extract.monitoring import init_sentry, capture_exception

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("workflow")


def extract_and_load(source, cleaner=None, full=False, to_parquet=False):
    """Extract a single source table, clean, and load.

    Args:
        source: Source module (e.g. extract.sources.run_number)
        cleaner: Optional cleaning function (df -> (valid_df, rejected_df))
        full: Full reload if True, incremental if False
        to_parquet: Save to Parquet instead of DB
    """
    table = source.TABLE
    columns = source.COLUMNS
    watermark_col = source.WATERMARK_COLUMN
    target = source.TARGET_TABLE

    # Get watermark
    wm = None if full else get_watermark(table)
    log.info(f"Extracting {table} (watermark: {wm or 'FULL'})")

    # Extract
    df = extract_table(table, columns, watermark_col, wm)

    if df.empty:
        log.info(f"  {table}: no new rows")
        return {"table": table, "extracted": 0, "valid": 0, "rejected": 0}

    log.info(f"  {table}: {len(df)} rows extracted")

    # Clean / validate
    rejected_df = None
    if cleaner:
        df, rejected_df = cleaner(df)
        if rejected_df is not None and not rejected_df.empty:
            load_rejected(rejected_df, target)

    # Load
    if to_parquet:
        load_to_parquet(df, target)
    else:
        mode = "replace" if full else "replace"  # SQLite doesn't support upsert well
        load_to_db(df, target, if_exists=mode)

    # Update watermark
    if not df.empty and watermark_col in [c.lower() for c in df.columns]:
        # Find the watermark column (case-insensitive)
        wm_col = [c for c in df.columns if c.lower() == watermark_col.lower()]
        if wm_col:
            max_wm = str(df[wm_col[0]].max())
            set_watermark(table, max_wm)

    result = {
        "table": table,
        "extracted": len(df),
        "valid": len(df),
        "rejected": len(rejected_df) if rejected_df is not None else 0,
    }
    return result


def run(full: bool = False, to_parquet: bool = False, report_only: bool = False):
    """Run the full daily workflow."""
    init_sentry()
    start = datetime.now()
    log.info("=" * 60)
    log.info("DAILY PRODUCTION DATA WORKFLOW")
    log.info(f"Mode: {'FULL RELOAD' if full else 'INCREMENTAL'}")
    log.info(f"Target: {'Parquet' if to_parquet else 'Database'}")
    log.info("=" * 60)

    results = []

    try:
        if not report_only:
            # Step 1: Extract RunNumber (production runs)
            log.info("\n--- Step 1: Production Runs ---")
            r = extract_and_load(run_number, cleaner=clean_run_numbers,
                                 full=full, to_parquet=to_parquet)
            results.append(r)

            # Step 2: Extract Transactions (per-pack weights)
            log.info("\n--- Step 2: Transactions ---")
            r = extract_and_load(transactions, cleaner=lambda df: (clean_transactions(df), None),
                                 full=full, to_parquet=to_parquet)
            results.append(r)

            # Step 3: Extract PLU (product master)
            log.info("\n--- Step 3: Products (PLU) ---")
            r = extract_and_load(plu, cleaner=lambda df: (clean_products(df), None),
                                 full=full, to_parquet=to_parquet)
            results.append(r)

            # Step 4: Extract Run Totals
            log.info("\n--- Step 4: Run Totals ---")
            r = extract_and_load(totals, full=full, to_parquet=to_parquet)
            results.append(r)
    except Exception as exc:
        capture_exception(exc)
        raise

    # Step 5: Summary
    elapsed = (datetime.now() - start).total_seconds()
    log.info("\n" + "=" * 60)
    log.info("WORKFLOW COMPLETE")
    log.info(f"Duration: {elapsed:.1f}s")
    log.info("-" * 60)

    total_extracted = 0
    total_rejected = 0
    for r in results:
        status = "OK" if r["rejected"] == 0 else f"WARN ({r['rejected']} rejected)"
        log.info(f"  {r['table']:25s} | {r['extracted']:6d} rows | {status}")
        total_extracted += r["extracted"]
        total_rejected += r["rejected"]

    log.info("-" * 60)
    log.info(f"  {'TOTAL':25s} | {total_extracted:6d} rows | {total_rejected} rejected")
    log.info("=" * 60)

    return results


if __name__ == "__main__":
    full = "--full" in sys.argv
    parquet = "--parquet" in sys.argv
    report_only = "--report-only" in sys.argv
    run(full=full, to_parquet=parquet, report_only=report_only)
