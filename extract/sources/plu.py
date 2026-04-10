"""Extract SI_OCM_PLU — product master / price look-up."""

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

TABLE = "SI_OCM_PLU"
WATERMARK_COLUMN = "Updated"
TARGET_TABLE = "raw_products"
