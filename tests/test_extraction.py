"""Tests for incremental extraction pipeline."""
import json
import os
import pytest
from datetime import datetime
from extract.incremental import build_query, load_state, save_state, validate
import pandas as pd


class TestBuildQuery:
    def test_full_reload(self):
        cols = ["RunNumber", "ProductionDate", "Description"]
        sql = build_query(cols)
        assert "SELECT RunNumber, ProductionDate, Description FROM RunNumber" in sql
        assert "WHERE" not in sql

    def test_incremental_with_watermark(self):
        cols = ["RunNumber", "ProductionDate"]
        sql = build_query(cols, watermark="2025-04-01 10:00:00")
        assert "WHERE Updated > '2025-04-01 10:00:00'" in sql

    def test_order_by_updated(self):
        sql = build_query(["RunNumber"], watermark=None)
        assert "ORDER BY Updated ASC" in sql


class TestState:
    def test_load_missing_state(self, tmp_path):
        os.environ["STATE_FILE"] = str(tmp_path / "missing.json")
        # Monkey-patch STATE_FILE
        import extract.incremental as mod
        old_sf = mod.STATE_FILE
        mod.STATE_FILE = str(tmp_path / "missing.json")
        state = mod.load_state()
        assert state["last_run"] is None
        mod.STATE_FILE = old_sf

    def test_save_and_load(self, tmp_path):
        import extract.incremental as mod
        old_sf = mod.STATE_FILE
        sf = str(tmp_path / "state.json")
        mod.STATE_FILE = sf
        mod.save_state({"last_run": "2025-04-01 10:00:00", "rows_extracted": 42})
        loaded = mod.load_state()
        assert loaded["last_run"] == "2025-04-01 10:00:00"
        assert loaded["rows_extracted"] == 42
        mod.STATE_FILE = old_sf


class TestValidation:
    def test_valid_rows_pass(self):
        df = pd.DataFrame([{
            "RunNumber": "003215",
            "ProductionDate": datetime(2025, 4, 1),
            "Description": "COD FILLET SKINLESS 200G",
            "ProductCode": "COD-200",
            "ProdLine": "Line 1",
            "ShiftCode": "DAY",
            "Spec": "SP-01",
            "Active": 1,
            "Complete": 1,
            "Created": datetime(2025, 4, 1, 6, 0),
            "Updated": datetime(2025, 4, 1, 14, 0),
        }])
        valid, rejected = validate(df)
        assert len(valid) == 1
        assert len(rejected) == 0
        assert valid.iloc[0]["species"] == "cod"
        assert valid.iloc[0]["product_type"] == "fillet"

    def test_empty_run_number_rejected(self):
        df = pd.DataFrame([{
            "RunNumber": "  ",
            "ProductionDate": datetime(2025, 4, 1),
            "Description": "COD FILLET",
            "ProductCode": None,
            "ProdLine": None,
            "ShiftCode": None,
            "Spec": None,
            "Active": 1,
            "Complete": 0,
            "Created": None,
            "Updated": None,
        }])
        valid, rejected = validate(df)
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_mixed_valid_and_invalid(self):
        df = pd.DataFrame([
            {
                "RunNumber": "003215",
                "ProductionDate": datetime(2025, 4, 1),
                "Description": "SALMON PORTIONS",
                "ProductCode": "SAL-01",
                "ProdLine": "Line 1",
                "ShiftCode": "DAY",
                "Spec": None,
                "Active": 1,
                "Complete": 1,
                "Created": datetime(2025, 4, 1),
                "Updated": datetime(2025, 4, 1),
            },
            {
                "RunNumber": "",
                "ProductionDate": datetime(2025, 4, 1),
                "Description": "BAD ROW",
                "ProductCode": None,
                "ProdLine": None,
                "ShiftCode": None,
                "Spec": None,
                "Active": 0,
                "Complete": 0,
                "Created": None,
                "Updated": None,
            },
        ])
        valid, rejected = validate(df)
        assert len(valid) == 1
        assert len(rejected) == 1
