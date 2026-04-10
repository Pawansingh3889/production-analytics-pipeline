"""Pydantic models for schema enforcement.

Legacy ERP systems dump everything as nvarchar. These models enforce
types at the Python boundary — bad data fails here, not in your dashboard.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class RunNumberRecord(BaseModel):
    """Validated production run record from ERP RunNumber table.

    Composite PK: (run_number, production_date)
    """
    run_number: str
    production_date: datetime
    description: str
    product_code: Optional[str] = None
    prod_line: Optional[str] = None
    shift_code: Optional[str] = None
    spec: Optional[str] = None
    active: bool = True
    complete: bool = False
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    # Derived fields (parsed from Description)
    species: Optional[str] = None
    product_type: Optional[str] = None

    @field_validator("run_number")
    @classmethod
    def run_number_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("run_number cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def clean_description(cls, v: str) -> str:
        return v.strip().upper() if v else ""

    @field_validator("active", "complete", mode="before")
    @classmethod
    def coerce_bool(cls, v):
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "y")
        return bool(v)

    def model_post_init(self, __context) -> None:
        """Parse species and product type from description after init."""
        if self.description:
            self.species = _extract_species(self.description)
            self.product_type = _extract_product_type(self.description)


# --- Extraction helpers ---

_SPECIES_PATTERNS = [
    (r"\bSALMON\b", "salmon"),
    (r"\bCOD\b", "cod"),
    (r"\bHAKE\b", "hake"),
    (r"\bHADDOCK\b", "haddock"),
    (r"\bSEABASS\b|SEA BASS\b", "seabass"),
    (r"\bMACKEREL\b", "mackerel"),
    (r"\bPRAWN\b", "prawn"),
    (r"\bTUNA\b", "tuna"),
    (r"\bPLAICE\b", "plaice"),
    (r"\bSOLE\b", "sole"),
    (r"\bTROUT\b", "trout"),
    (r"\bPOLLOCK\b", "pollock"),
]

_TYPE_PATTERNS = [
    (r"\bSMOKED\b", "smoked"),
    (r"\bBREADED\b", "breaded"),
    (r"\bBATTERED\b", "battered"),
    (r"\bFILLET", "fillet"),
    (r"\bLOIN", "loin"),
    (r"\bPORTION", "portion"),
    (r"\bSTEAK", "steak"),
    (r"\bFISH CAKE|FISHCAKE", "fish_cake"),
    (r"\bGOUJON", "goujon"),
    (r"\bWHOLE\b", "whole"),
]


def _extract_species(desc: str) -> Optional[str]:
    for pattern, species in _SPECIES_PATTERNS:
        if re.search(pattern, desc, re.IGNORECASE):
            return species
    return None


def _extract_product_type(desc: str) -> Optional[str]:
    for pattern, ptype in _TYPE_PATTERNS:
        if re.search(pattern, desc, re.IGNORECASE):
            return ptype
    return None
