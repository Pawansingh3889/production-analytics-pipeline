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
        table: Source table name (e.g. 'RunNumber', 'erp_transactions')
        columns: Columns to extract (never SELECT *)
        watermark_col: Column used for incremental loading
        watermark_value: Only rows where watermark_col > this value
        batch_size: Rows per fetch batch
        source_db: SQLAlchemy connection string

    Returns:
        DataFrame with extracted rows
    """
    # Safety: validate query is read-only
    _validate_extraction(table, columns, watermark_col)

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


def _validate_extraction(table: str, columns: list[str], watermark_col: str) -> None:
    """Safety checks before any extraction query runs.

    Prevents:
    - SQL injection via table/column names
    - SELECT * (must specify columns)
    - Write operations (only SELECT allowed)
    - Wildcard columns
    """
    import re

    # Block dangerous characters (always blocked regardless of context)
    CHAR_BLOCKED = [";", "--", "/*", "*/", "xp_", "sp_"]

    # Block dangerous keywords (matched as whole words to avoid false positives
    # like "Updated" matching "UPDATE")
    KEYWORD_BLOCKED = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER",
                       "TRUNCATE", "EXEC", "EXECUTE"]

    all_names = [table, watermark_col] + columns
    for name in all_names:
        # Check dangerous characters
        for blocked in CHAR_BLOCKED:
            if blocked in name:
                raise ValueError(
                    f"BLOCKED: '{name}' contains forbidden character '{blocked}'. "
                    f"This extractor is read-only."
                )

        # Check dangerous keywords (whole word match)
        for blocked in KEYWORD_BLOCKED:
            pattern = rf"\b{re.escape(blocked)}\b"
            if re.search(pattern, name, re.IGNORECASE):
                raise ValueError(
                    f"BLOCKED: '{name}' contains forbidden keyword '{blocked}'. "
                    f"This extractor is read-only."
                )

    # Block SELECT *
    if "*" in columns:
        raise ValueError(
            "SELECT * is not allowed. Specify exact columns to extract. "
            "varchar(max) columns can crash your pipeline memory."
        )

    # Block empty columns
    if not columns:
        raise ValueError("No columns specified for extraction.")

    # Log the query for audit trail
    _log_query(table, columns, watermark_col)


def _log_query(table: str, columns: list[str], watermark_col: str) -> None:
    """Write extraction query to audit log."""
    import logging
    log = logging.getLogger("extractor.audit")
    log.info(f"EXTRACT {table} [{len(columns)} cols] watermark={watermark_col}")


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
