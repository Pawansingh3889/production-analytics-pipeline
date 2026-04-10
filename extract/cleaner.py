"""Data cleaning and standardisation.

Takes raw ERP data and produces clean, typed DataFrames.
This is the boundary between messy varchar ERP data and your clean warehouse.
"""
from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from models.run_number import RunNumberRecord


def clean_run_numbers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate and clean RunNumber rows through Pydantic.

    Returns:
        (valid_df, rejected_df)
    """
    valid = []
    rejected = []

    for _, row in df.iterrows():
        try:
            record = RunNumberRecord(
                run_number=str(row.get("RunNumber", "")),
                production_date=row.get("ProductionDate"),
                description=str(row.get("Description", "")),
                product_code=_safe_str(row.get("ProductCode")),
                prod_line=_safe_str(row.get("ProdLine")),
                shift_code=_safe_str(row.get("ShiftCode")),
                spec=_safe_str(row.get("Spec")),
                active=row.get("Active", 1),
                complete=row.get("Complete", 0),
                created=row.get("Created"),
                updated=row.get("Updated"),
            )
            valid.append(record.model_dump())
        except Exception as e:
            rejected.append({**row.to_dict(), "_error": str(e)})

    return (
        pd.DataFrame(valid) if valid else pd.DataFrame(),
        pd.DataFrame(rejected) if rejected else pd.DataFrame(),
    )


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean transaction data — standardise types, calculate net/overweight."""
    if df.empty:
        return df

    df = df.copy()

    # Type casting
    for col in ["Weight", "TargetWeight", "Tare", "NetWeight", "Overweight"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Calculate net weight if missing
    if "NetWeight" in df.columns and "Weight" in df.columns and "Tare" in df.columns:
        mask = df["NetWeight"].isna()
        df.loc[mask, "NetWeight"] = df.loc[mask, "Weight"] - df.loc[mask, "Tare"]

    # Calculate overweight if missing
    if "Overweight" in df.columns and "NetWeight" in df.columns and "TargetWeight" in df.columns:
        mask = df["Overweight"].isna()
        df.loc[mask, "Overweight"] = df.loc[mask, "NetWeight"] - df.loc[mask, "TargetWeight"]

    # Standardise column names to snake_case
    df.columns = [_to_snake(c) for c in df.columns]

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Clean PLU/product data — trim strings, standardise allergens."""
    if df.empty:
        return df

    df = df.copy()

    # Trim all string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Standardise allergens to lowercase, comma-separated
    if "Allergens" in df.columns:
        df["Allergens"] = df["Allergens"].str.lower().str.strip()

    df.columns = [_to_snake(c) for c in df.columns]
    return df


def _safe_str(val) -> Optional[str]:
    """Convert to string safely, return None for empty/null."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def _to_snake(name: str) -> str:
    """Convert PascalCase/camelCase to snake_case."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()
