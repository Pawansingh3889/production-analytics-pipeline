"""Incremental extraction from ERP RunNumber table.

Uses watermark pattern: only pull rows where Updated > last_run_timestamp.
This prevents full-table scans on a production ERP system.

Usage:
    python -m extract.incremental              # incremental (default)
    python -m extract.incremental --full        # full reload
    python -m extract.incremental --to-parquet  # save to parquet instead of DB
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text

from extract.config import (
    BATCH_SIZE,
    MAX_UDF_LENGTH,
    RUN_NUMBER_COLUMNS,
    SOURCE_DB,
    STATE_FILE,
    TARGET_DB,
)
from models.run_number import RunNumberRecord


def load_state() -> dict:
    """Load pipeline state (last successful run timestamp)."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_run": None, "rows_extracted": 0, "runs": 0}


def save_state(state: dict) -> None:
    """Save pipeline state after successful run."""
    os.makedirs(os.path.dirname(STATE_FILE) or ".", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def build_query(columns: list[str], watermark: Optional[str] = None) -> str:
    """Build extraction query with optional incremental watermark.

    Never SELECT * — only pull columns we need.
    """
    cols = ", ".join(columns)
    query = f"SELECT {cols} FROM RunNumber"

    if watermark:
        query += f" WHERE Updated > '{watermark}'"

    query += " ORDER BY Updated ASC"
    return query


def extract(full_reload: bool = False) -> pd.DataFrame:
    """Extract data from source ERP database.

    Args:
        full_reload: If True, ignore watermark and pull all rows.

    Returns:
        DataFrame with raw extracted data.
    """
    state = load_state()
    watermark = None if full_reload else state.get("last_run")

    engine = create_engine(SOURCE_DB)
    query = build_query(RUN_NUMBER_COLUMNS, watermark)

    print(f"[EXTRACT] Source: {SOURCE_DB}")
    print(f"[EXTRACT] Watermark: {watermark or 'FULL RELOAD'}")
    print(f"[EXTRACT] Query: {query[:100]}...")

    # Batch fetch to avoid memory issues with varchar(max) columns
    chunks = []
    with engine.connect() as conn:
        result = conn.execute(text(query))
        while True:
            rows = result.fetchmany(BATCH_SIZE)
            if not rows:
                break
            chunk = pd.DataFrame(rows, columns=RUN_NUMBER_COLUMNS)
            chunks.append(chunk)
            print(f"[EXTRACT] Fetched batch: {len(chunk)} rows")

    if not chunks:
        print("[EXTRACT] No new rows found.")
        return pd.DataFrame()

    df = pd.concat(chunks, ignore_index=True)
    print(f"[EXTRACT] Total rows: {len(df)}")
    return df


def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate rows through Pydantic model. Split into valid + rejected.

    This is where bad ERP data fails — not in your dashboard.
    """
    valid_rows = []
    rejected_rows = []

    for _, row in df.iterrows():
        try:
            record = RunNumberRecord(
                run_number=str(row.get("RunNumber", "")),
                production_date=row.get("ProductionDate"),
                description=str(row.get("Description", "")),
                product_code=str(row.get("ProductCode", "")) if row.get("ProductCode") else None,
                prod_line=str(row.get("ProdLine", "")) if row.get("ProdLine") else None,
                shift_code=str(row.get("ShiftCode", "")) if row.get("ShiftCode") else None,
                spec=str(row.get("Spec", "")) if row.get("Spec") else None,
                active=row.get("Active", 1),
                complete=row.get("Complete", 0),
                created=row.get("Created"),
                updated=row.get("Updated"),
            )
            valid_rows.append(record.model_dump())
        except Exception as e:
            rejected_rows.append({**row.to_dict(), "_error": str(e)})

    valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
    rejected_df = pd.DataFrame(rejected_rows) if rejected_rows else pd.DataFrame()

    print(f"[VALIDATE] Valid: {len(valid_df)} | Rejected: {len(rejected_df)}")
    return valid_df, rejected_df


def load_to_db(df: pd.DataFrame) -> int:
    """Load validated data to target database with upsert logic.

    Composite PK (run_number, production_date) — must handle duplicates.
    """
    if df.empty:
        return 0

    engine = create_engine(TARGET_DB)

    # Replace mode for SQLite — drops and recreates with fresh data
    # For PostgreSQL, use ON CONFLICT (run_number, production_date) DO UPDATE
    df.to_sql("run_numbers", engine, if_exists="replace", index=False)

    print(f"[LOAD] Upserted {len(df)} rows to {TARGET_DB}")
    return len(df)


def load_to_parquet(df: pd.DataFrame, path: str = "data/run_numbers.parquet") -> None:
    """Save validated data to Parquet file (columnar, compressed)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    df.to_parquet(path, index=False, engine="pyarrow")
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"[PARQUET] Saved {len(df)} rows to {path} ({size_mb:.2f} MB)")


def run(full_reload: bool = False, to_parquet: bool = False) -> dict:
    """Run the full ETL pipeline: extract -> validate -> load."""
    start = datetime.now()

    # Extract
    raw_df = extract(full_reload)
    if raw_df.empty:
        return {"status": "no_data", "rows": 0}

    # Validate (Pydantic schema enforcement)
    valid_df, rejected_df = validate(raw_df)

    # Save rejected rows for investigation
    if not rejected_df.empty:
        rejected_df.to_csv("data/rejected_rows.csv", index=False)
        print(f"[REJECT] Saved {len(rejected_df)} rejected rows to data/rejected_rows.csv")

    # Load
    if to_parquet:
        load_to_parquet(valid_df)
    else:
        load_to_db(valid_df)

    # Update state
    if not valid_df.empty and "updated" in valid_df.columns:
        max_updated = valid_df["updated"].max()
    else:
        max_updated = datetime.now()

    state = {
        "last_run": str(max_updated),
        "rows_extracted": len(valid_df),
        "rejected": len(rejected_df),
        "runs": load_state().get("runs", 0) + 1,
        "duration_seconds": (datetime.now() - start).total_seconds(),
    }
    save_state(state)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"[DONE] Pipeline complete in {elapsed:.1f}s")
    return state


if __name__ == "__main__":
    full = "--full" in sys.argv
    parquet = "--to-parquet" in sys.argv
    run(full_reload=full, to_parquet=parquet)
