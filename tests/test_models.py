"""Tests for Pydantic schema enforcement models."""
from datetime import datetime

import pytest

from models.run_number import RunNumberRecord, _extract_product_type, _extract_species


class TestRunNumberRecord:
    def test_valid_record(self):
        r = RunNumberRecord(
            run_number="003215",
            production_date=datetime(2025, 4, 1),
            description="DEF- MSC HAKE FILLETS",
        )
        assert r.run_number == "003215"
        assert r.species == "hake"
        assert r.product_type == "fillet"

    def test_empty_run_number_rejected(self):
        with pytest.raises(ValueError):
            RunNumberRecord(
                run_number="  ",
                production_date=datetime(2025, 4, 1),
                description="COD FILLET",
            )

    def test_description_uppercased(self):
        r = RunNumberRecord(
            run_number="003216",
            production_date=datetime(2025, 4, 1),
            description="  salmon portions  ",
        )
        assert r.description == "SALMON PORTIONS"
        assert r.species == "salmon"
        assert r.product_type == "portion"

    def test_bool_coercion_from_int(self):
        r = RunNumberRecord(
            run_number="003217",
            production_date=datetime(2025, 4, 1),
            description="COD LOIN",
            active=1,
            complete=0,
        )
        assert r.active is True
        assert r.complete is False

    def test_bool_coercion_from_string(self):
        r = RunNumberRecord(
            run_number="003218",
            production_date=datetime(2025, 4, 1),
            description="SEABASS FILLETS",
            active="true",
            complete="false",
        )
        assert r.active is True
        assert r.complete is False

    def test_optional_fields_default_none(self):
        r = RunNumberRecord(
            run_number="003219",
            production_date=datetime(2025, 4, 1),
            description="PRAWN RING",
        )
        assert r.product_code is None
        assert r.prod_line is None
        assert r.shift_code is None

    def test_smoked_product_type(self):
        r = RunNumberRecord(
            run_number="003220",
            production_date=datetime(2025, 4, 1),
            description="SMOKED HADDOCK FILLET 170G",
        )
        assert r.species == "haddock"
        assert r.product_type == "smoked"  # smoked takes priority

    def test_breaded_product(self):
        r = RunNumberRecord(
            run_number="003221",
            production_date=datetime(2025, 4, 1),
            description="BREADED COD GOUJONS 300G",
        )
        assert r.species == "cod"
        assert r.product_type == "breaded"

    def test_unknown_species(self):
        r = RunNumberRecord(
            run_number="003222",
            production_date=datetime(2025, 4, 1),
            description="SEAFOOD MIX DELUXE",
        )
        assert r.species is None

    def test_sea_bass_two_words(self):
        r = RunNumberRecord(
            run_number="003223",
            production_date=datetime(2025, 4, 1),
            description="SEA BASS FILLETS SKIN ON",
        )
        assert r.species == "seabass"


class TestSpeciesExtraction:
    @pytest.mark.parametrize("desc,expected", [
        ("MSC HAKE FILLETS", "hake"),
        ("RSPCA SALMON PORTIONS", "salmon"),
        ("COD FILLET SKINLESS", "cod"),
        ("SMOKED HADDOCK", "haddock"),
        ("MACKEREL PEPPERED", "mackerel"),
        ("TUNA STEAK 150G", "tuna"),
        ("PLAICE FILLET", "plaice"),
        ("POLLOCK MSC 180G", "pollock"),
        ("RANDOM PRODUCT", None),
    ])
    def test_species(self, desc, expected):
        assert _extract_species(desc) == expected


class TestProductTypeExtraction:
    @pytest.mark.parametrize("desc,expected", [
        ("COD FILLET SKINLESS", "fillet"),
        ("SALMON LOIN 200G", "loin"),
        ("SALMON PORTIONS 130G", "portion"),
        ("TUNA STEAK", "steak"),
        ("SMOKED HADDOCK", "smoked"),
        ("BREADED COD", "breaded"),
        ("BATTERED COD", "battered"),
        ("FISH CAKE 300G", "fish_cake"),
        ("COD GOUJONS", "goujon"),
        ("WHOLE PLAICE", "whole"),
        ("PRAWN RING", None),
    ])
    def test_product_type(self, desc, expected):
        assert _extract_product_type(desc) == expected
