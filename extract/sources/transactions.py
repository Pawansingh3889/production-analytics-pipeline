"""Extract erp_transactions — per-pack weights from inline scales."""

COLUMNS = [
    "TransNo",
    "RunNumber",
    "TransDate",
    "ProductCode",
    "Weight",
    "TargetWeight",
    "Tare",
    "NetWeight",
    "Overweight",
    "Barcode",
    "LabelPrinted",
    "ScannerPass",
    "ProdLine",
    "OperatorID",
]

TABLE = "erp_transactions"
WATERMARK_COLUMN = "TransDate"
TARGET_TABLE = "raw_transactions"
