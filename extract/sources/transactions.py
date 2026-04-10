"""Extract SI_OCM_TRANS — per-pack weights from inline scales."""

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

TABLE = "SI_OCM_TRANS"
WATERMARK_COLUMN = "TransDate"
TARGET_TABLE = "raw_transactions"
