"""Extract SI_OCM_TOTALS — run-level aggregates."""

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

TABLE = "SI_OCM_TOTALS"
WATERMARK_COLUMN = "Updated"
TARGET_TABLE = "raw_run_totals"
