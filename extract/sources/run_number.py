"""Extract RunNumber table — production runs with composite PK."""

COLUMNS = [
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
]

TABLE = "RunNumber"
WATERMARK_COLUMN = "Updated"
TARGET_TABLE = "raw_run_numbers"
