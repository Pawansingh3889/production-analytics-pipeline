"""Load clean data to target storage.

Supports:
- Parquet files (partitioned by date)
- DuckDB (local analytics)
- SQLite (development)
- PostgreSQL (production warehouse)
"""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

from extract.config import TARGET_DB


def load_to_parquet(
    df: pd.DataFrame,
    table_name: str,
    base_path: str = "data/warehouse",
) -> str:
    """Save DataFrame to partitioned Parquet file.

    Structure: data/warehouse/{table_name}/{date}.parquet
    """
    if df.empty:
        return ""

    date_str = datetime.now().strftime("%Y-%m-%d")
    dir_path = os.path.join(base_path, table_name)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{date_str}.parquet")
    df.to_parquet(file_path, index=False, engine="pyarrow")

    size_kb = os.path.getsize(file_path) / 1024
    print(f"  [{table_name}] Saved {len(df)} rows to {file_path} ({size_kb:.1f} KB)")
    return file_path


def load_to_db(
    df: pd.DataFrame,
    table_name: str,
    target_db: str = TARGET_DB,
    if_exists: str = "replace",
) -> int:
    """Load DataFrame to target database.

    Args:
        df: Clean DataFrame to load
        table_name: Target table name
        target_db: SQLAlchemy connection string
        if_exists: 'replace' for full reload, 'append' for incremental
    """
    if df.empty:
        return 0

    engine = create_engine(target_db)
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    print(f"  [{table_name}] Loaded {len(df)} rows to {target_db}")
    return len(df)


def load_rejected(df: pd.DataFrame, table_name: str) -> None:
    """Save rejected rows for investigation."""
    if df.empty:
        return

    path = f"data/rejected/{table_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  [{table_name}] {len(df)} rejected rows saved to {path}")
