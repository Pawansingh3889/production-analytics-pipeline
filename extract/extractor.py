"""Generic incremental extractor for any ERP table.

Given a source config (table name, columns, watermark column),
extracts rows incrementally and returns a DataFrame.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text

from extract.config import BATCH_SIZE, SOURCE_DB, STATE_FILE


def _state_path() -> str:
    return STATE_FILE


def load_state() -> dict:
    path = _state_path()
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    path = _state_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)


def extract_table(
    table: str,
    columns: list[str],
    watermark_col: str,
    watermark_value: Optional[str] = None,
    batch_size: int = BATCH_SIZE,
    source_db: str = SOURCE_DB,
) -> pd.DataFrame:
    """Extract rows from a single ERP table.

    Args:
        table: Source table name (e.g. 'RunNumber', 'SI_OCM_TRANS')
        columns: Columns to extract (never SELECT *)
        watermark_col: Column used for incremental loading
        watermark_value: Only rows where watermark_col > this value
        batch_size: Rows per fetch batch
        source_db: SQLAlchemy connection string

    Returns:
        DataFrame with extracted rows
    """
    cols = ", ".join(columns)
    query = f"SELECT {cols} FROM {table}"
    if watermark_value:
        query += f" WHERE {watermark_col} > '{watermark_value}'"
    query += f" ORDER BY {watermark_col} ASC"

    engine = create_engine(source_db)
    chunks = []

    with engine.connect() as conn:
        result = conn.execute(text(query))
        while True:
            rows = result.fetchmany(batch_size)
            if not rows:
                break
            chunk = pd.DataFrame(rows, columns=columns)
            chunks.append(chunk)

    if not chunks:
        return pd.DataFrame(columns=columns)

    return pd.concat(chunks, ignore_index=True)


def get_watermark(table: str) -> Optional[str]:
    """Get last watermark for a table from state file."""
    state = load_state()
    return state.get(f"watermark_{table}")


def set_watermark(table: str, value: str) -> None:
    """Save watermark for a table to state file."""
    state = load_state()
    state[f"watermark_{table}"] = str(value)
    state[f"last_run_{table}"] = datetime.now().isoformat()
    save_state(state)
