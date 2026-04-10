"""Extraction pipeline configuration.

Connection strings use environment variables — never hardcode credentials.
Defaults point to local SQLite for safe development.
"""
import os
import sys

# Source: SQL Server (ERP system, read-only)
# Example: mssql+pyodbc://readonly:pass@SERVER/SI_OCM_23?driver=ODBC+Driver+17+for+SQL+Server
SOURCE_DB = os.getenv("SOURCE_DB", "sqlite:///data/mock_erp.db")

# Target: where cleaned data lands
# Example: postgresql://user:pass@localhost/production_dw
TARGET_DB = os.getenv("TARGET_DB", "sqlite:///data/production_dw.db")

# Safety: block accidental connection to production with write user
if "mssql" in SOURCE_DB and "readonly" not in SOURCE_DB.lower() and "reader" not in SOURCE_DB.lower():
    if "sa:" in SOURCE_DB or "SA:" in SOURCE_DB:
        print("ERROR: SOURCE_DB uses SA (admin) credentials.")
        print("       Use a read-only user: pipeline_reader or readonly")
        print("       Never connect to production ERP as admin.")
        sys.exit(1)

# Incremental load state file
STATE_FILE = os.getenv("STATE_FILE", "data/pipeline_state.json")

# Extraction settings
BATCH_SIZE = 5000         # rows per fetch — prevents memory issues with varchar(max)
MAX_UDF_LENGTH = 500      # truncate UDF fields beyond this length

# Columns to extract (never SELECT * on a production ERP)
RUN_NUMBER_COLUMNS = [
    "RunNumber",
    "ProductionDate",
    "Description",
    "ProductCode",
    "ProdLine",
    "ShiftCode",
    "Spec",
    "Active",
    "Complete",
    "Created",
    "Updated",
    # UDFs — only pull the ones you actually need
    # "OCM_UDF_Value1",
    # "OCM_UDF_Value2",
]
