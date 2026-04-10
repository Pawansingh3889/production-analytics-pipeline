"""Tests for extraction safety guards."""
import pytest
from extract.extractor import _validate_extraction


class TestValidateExtraction:
    def test_valid_extraction_passes(self):
        _validate_extraction("RunNumber", ["RunNumber", "Description"], "Updated")

    def test_select_star_blocked(self):
        with pytest.raises(ValueError, match="SELECT .* is not allowed"):
            _validate_extraction("RunNumber", ["*"], "Updated")

    def test_empty_columns_blocked(self):
        with pytest.raises(ValueError, match="No columns specified"):
            _validate_extraction("RunNumber", [], "Updated")

    def test_drop_in_table_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("DROP TABLE runs", ["col1"], "Updated")

    def test_delete_keyword_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["DELETE"], "Updated")

    def test_insert_keyword_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["col1"], "INSERT")

    def test_sql_comment_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["col1 --"], "Updated")

    def test_semicolon_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber; SELECT 1", ["col1"], "Updated")

    def test_exec_keyword_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["EXEC"], "Updated")

    def test_xp_prefix_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["xp_cmdshell"], "Updated")

    def test_truncate_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("TRUNCATE", ["col1"], "Updated")

    def test_alter_keyword_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["ALTER"], "Updated")

    def test_update_keyword_blocked(self):
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_extraction("RunNumber", ["UPDATE"], "Updated")

    def test_updated_column_allowed(self):
        """'Updated' should NOT trigger the UPDATE block (whole-word match)."""
        _validate_extraction("RunNumber", ["Description"], "Updated")

    def test_normal_columns_pass(self):
        _validate_extraction("SI_OCM_TRANS", ["TransNo", "RunNumber", "Weight"], "TransDate")
