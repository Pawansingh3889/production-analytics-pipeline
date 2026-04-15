"""Extract erp_totals — run-level aggregates."""

COLUMNS = [
    "RunNumber",
    "TotalPacks",
    "TotalWeight",
    "AvgWeight",
    "MinWeight",
    "MaxWeight",
    "StdDev",
    "Giveaway",
    "GiveawayPct",
    "RejectCount",
    "DowntimeMins",
    "Updated",
]

TABLE = "erp_totals"
WATERMARK_COLUMN = "Updated"
TARGET_TABLE = "raw_run_totals"
