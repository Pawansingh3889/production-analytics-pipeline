"""Extract erp_products — product master / price look-up."""

COLUMNS = [
    "PLUNumber",
    "Description",
    "ProductCode",
    "Category",
    "Species",
    "PackSize",
    "ShelfLife",
    "Allergens",
    "Active",
    "Updated",
]

TABLE = "erp_products"
WATERMARK_COLUMN = "Updated"
TARGET_TABLE = "raw_products"
