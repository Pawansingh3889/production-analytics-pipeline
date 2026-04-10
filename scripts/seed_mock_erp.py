"""Seed a mock ERP database for testing the extraction pipeline.

Creates a SQLite database that mimics the RunNumber table structure
from a fish processing ERP system.
"""
import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mock_erp.db")


def seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS RunNumber;

        CREATE TABLE RunNumber (
            RunNumber TEXT NOT NULL,
            ProductionDate TEXT NOT NULL,
            Description TEXT,
            ProductCode TEXT,
            ProdLine TEXT,
            ShiftCode TEXT,
            Spec TEXT,
            Active INTEGER DEFAULT 1,
            Complete INTEGER DEFAULT 0,
            Created TEXT,
            Updated TEXT,
            PRIMARY KEY (RunNumber, ProductionDate)
        );
    """)

    # Realistic fish product descriptions (as they appear in ERP systems)
    products = [
        ("DEF- MSC HAKE FILLETS", "HAKE-FIL-01", "Line 1"),
        ("SEABASS FILLETS SKIN ON", "SBAS-FIL-02", "Line 2"),
        ("RSPCA SALMON PORTIONS 130G", "SAL-POR-03", "Line 1"),
        ("COD FILLET SKINLESS 200G", "COD-FIL-04", "Line 3"),
        ("SMOKED HADDOCK FILLET 170G", "HAD-SMK-05", "Smoke Line"),
        ("MSC COD LOIN BONELESS 280G", "COD-LON-06", "Line 2"),
        ("BREADED COD GOUJONS 300G", "COD-GOU-07", "VA Line"),
        ("SALMON DARNES 200G SKIN ON", "SAL-DAR-08", "Line 1"),
        ("MACKEREL FILLET PEPPERED", "MAC-FIL-09", "Smoke Line"),
        ("PRAWN RING COOKED 200G", "PRN-RNG-10", "VA Line"),
        ("FISH PIE MIX 400G", "MIX-PIE-11", "VA Line"),
        ("PLAICE FILLET WHOLE", "PLC-FIL-12", "Line 3"),
        ("TUNA STEAK 150G", "TUN-STK-13", "Line 2"),
        ("SOLE FILLET LEMON", "SOL-FIL-14", "Line 1"),
        ("POLLOCK FILLET MSC 180G", "POL-FIL-15", "Line 3"),
    ]

    shifts = ["DAY", "NIGHT", "LATE"]
    specs = ["SP-STD-01", "SP-PRM-02", "SP-ECO-03", "SP-ORG-04"]

    now = datetime.now()
    run_id = 3200
    rows = []

    for day_offset in range(90):  # 90 days of data
        date = now - timedelta(days=day_offset)
        date_str = date.strftime("%Y-%m-%d")

        # 5-12 runs per day
        for _ in range(random.randint(5, 12)):
            run_id += 1
            run_num = f"{run_id:06d}"
            prod = random.choice(products)
            shift = random.choice(shifts)
            spec = random.choice(specs)
            active = 1 if day_offset < 2 else random.choice([0, 1, 1, 1, 1])
            complete = 0 if active and day_offset < 1 else 1

            created = date.replace(
                hour=random.randint(5, 7),
                minute=random.randint(0, 59)
            )
            updated = created + timedelta(
                hours=random.randint(1, 10),
                minutes=random.randint(0, 59)
            )

            rows.append((
                run_num, date_str, prod[0], prod[1], prod[2],
                shift, spec, active, complete,
                created.strftime("%Y-%m-%d %H:%M:%S"),
                updated.strftime("%Y-%m-%d %H:%M:%S"),
            ))

    c.executemany(
        "INSERT INTO RunNumber VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        rows
    )

    conn.commit()
    conn.close()

    print(f"Mock ERP database created: {DB_PATH}")
    print(f"  RunNumber rows: {len(rows)}")
    print(f"  Date range: {(now - timedelta(days=90)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    print(f"  Products: {len(products)}")


if __name__ == "__main__":
    seed()
