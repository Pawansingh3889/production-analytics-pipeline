"""Export mart-level production data to CSV files for Power BI Desktop import.

Reads from the production_dw SQLite database (or any SQLAlchemy-compatible
target) and writes CSV files into reports/powerbi/. Each mart table gets its
own CSV that can be loaded via Power BI Desktop -> Get Data -> Text/CSV.
"""

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_DB = os.getenv(
    "TARGET_DB",
    "sqlite:///data/production_dw.db",
)

OUTPUT_DIR = Path(__file__).resolve().parent / "powerbi"

# Mart tables to export.  The key is the filename stem, the value is the SQL
# query.  If a dbt-materialised mart table exists we pull from it directly;
# otherwise we fall back to raw tables with equivalent aggregations so the
# export still produces useful output before dbt has been run.

MART_QUERIES: dict[str, str] = {
    "daily_yield": """
        SELECT
            r.production_date,
            r.shift_code,
            r.prod_line,
            r.species,
            r.product_type,
            COUNT(*)            AS run_count,
            r.complete
        FROM run_numbers r
        GROUP BY
            r.production_date,
            r.shift_code,
            r.prod_line,
            r.species,
            r.product_type,
            r.complete
        ORDER BY r.production_date
    """,
    "shift_productivity": """
        SELECT
            r.production_date,
            r.shift_code,
            r.prod_line,
            COUNT(*)          AS runs,
            SUM(t.TotalPacks) AS total_packs,
            ROUND(SUM(t.TotalWeight), 2) AS total_weight_kg,
            ROUND(AVG(t.GiveawayPct), 2) AS avg_giveaway_pct,
            SUM(t.DowntimeMins)          AS total_downtime_mins
        FROM run_numbers r
        LEFT JOIN raw_run_totals t ON r.run_number = t.RunNumber
        GROUP BY r.production_date, r.shift_code, r.prod_line
        ORDER BY r.production_date
    """,
    "compliance_checks": """
        SELECT
            r.run_number,
            r.production_date,
            r.prod_line,
            r.species,
            r.product_type,
            r.shift_code,
            CASE WHEN r.complete = 1 THEN 'complete' ELSE 'incomplete' END AS status,
            CASE
                WHEN t.GiveawayPct > 3.0 THEN 'WARNING: giveaway > 3%'
                ELSE 'OK'
            END AS giveaway_check,
            t.GiveawayPct AS giveaway_pct,
            t.RejectCount AS reject_count
        FROM run_numbers r
        LEFT JOIN raw_run_totals t ON r.run_number = t.RunNumber
        ORDER BY r.production_date
    """,
}

# If dbt mart tables are materialised, prefer them over the fallback queries.
DBT_MART_TABLES: dict[str, str] = {
    "daily_yield": "fct_daily_yield",
    "shift_productivity": "fct_shift_productivity",
    "compliance_checks": "fct_compliance_checks",
}


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------


def _table_exists(engine, table_name: str) -> bool:
    """Return True if *table_name* exists in the database."""
    return table_name in inspect(engine).get_table_names()


def export_mart(engine, name: str, query: str, output_dir: Path) -> Path:
    """Run *query* against *engine* and write the result to a CSV file.

    Returns the path to the written CSV.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / f"{name}.csv"
    df = pd.read_sql_query(text(query), engine)
    df.to_csv(dest, index=False)
    return dest


def main() -> None:
    """Export all mart-level datasets to CSV for Power BI."""
    engine = create_engine(TARGET_DB)

    print("Power BI CSV Export")
    print("=" * 50)
    print(f"Source : {TARGET_DB}")
    print(f"Output : {OUTPUT_DIR}")
    print()

    exported: list[tuple[str, Path, int]] = []

    for name, fallback_query in MART_QUERIES.items():
        dbt_table = DBT_MART_TABLES.get(name)

        # Use the dbt mart table when it exists; otherwise use fallback SQL.
        if dbt_table and _table_exists(engine, dbt_table):
            query = f"SELECT * FROM {dbt_table}"
        else:
            query = fallback_query

        dest = export_mart(engine, name, query, OUTPUT_DIR)
        row_count = sum(1 for _ in open(dest)) - 1  # subtract header
        exported.append((name, dest, row_count))

    print(f"{'Dataset':<25} {'Rows':>8}  Path")
    print("-" * 70)
    for name, path, rows in exported:
        print(f"{name:<25} {rows:>8}  {path}")

    print()
    print(f"Exported {len(exported)} file(s).  "
          "Open Power BI Desktop -> Get Data -> Text/CSV to import.")


if __name__ == "__main__":
    main()
