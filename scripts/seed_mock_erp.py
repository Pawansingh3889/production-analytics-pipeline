"""Seed a mock ERP database for testing the extraction pipeline.

Creates a SQLite database that mimics the RunNumber table structure
from a fish processing ERP system.
"""
import os
import random
import sqlite3
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

    # === SI_OCM_TRANS (per-pack weights) ===
    c.executescript("""
        DROP TABLE IF EXISTS SI_OCM_TRANS;
        CREATE TABLE SI_OCM_TRANS (
            TransNo INTEGER PRIMARY KEY AUTOINCREMENT,
            RunNumber TEXT, TransDate TEXT, ProductCode TEXT,
            Weight REAL, TargetWeight REAL, Tare REAL,
            NetWeight REAL, Overweight REAL, Barcode TEXT,
            LabelPrinted INTEGER, ScannerPass INTEGER,
            ProdLine TEXT, OperatorID TEXT
        );
    """)
    # Map product codes to realistic target weights
    product_weights = {
        'HAKE-FIL-01': 240, 'SBAS-FIL-02': 180, 'SAL-POR-03': 130,
        'COD-FIL-04': 200, 'HAD-SMK-05': 170, 'COD-LON-06': 280,
        'COD-GOU-07': 300, 'SAL-DAR-08': 200, 'MAC-FIL-09': 150,
        'PRN-RNG-10': 200, 'MIX-PIE-11': 400, 'PLC-FIL-12': 240,
        'TUN-STK-13': 150, 'SOL-FIL-14': 200, 'POL-FIL-15': 180,
    }
    trans_count = 0
    for row in rows:
        run_num, date_str, desc, pcode, pline = row[0], row[1], row[2], row[3], row[4]
        target_wt = product_weights.get(pcode, 200)
        for _ in range(random.randint(10, 25)):
            # Realistic: most packs 1-5g over target, occasional 1-3g under
            wt = round(target_wt + random.gauss(3, 4), 1)
            wt = max(target_wt - 5, wt)  # minimum weight close to target
            tare = round(random.uniform(4, 6), 1)  # tray tare ~5g
            net = round(wt - tare, 1)
            over = round(net - target_wt, 1)
            c.execute(
                "INSERT INTO SI_OCM_TRANS (RunNumber, TransDate, ProductCode, Weight, TargetWeight, Tare, NetWeight, Overweight, Barcode, LabelPrinted, ScannerPass, ProdLine, OperatorID) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_num, date_str, pcode, wt, target_wt, tare, net, over,
                 f"501234{random.randint(1000000,9999999)}", 1,
                 1 if random.random() > 0.02 else 0, pline, f"OP{random.randint(1,8):02d}")
            )
            trans_count += 1

    # === SI_OCM_PLU (product master) ===
    c.executescript("""
        DROP TABLE IF EXISTS SI_OCM_PLU;
        CREATE TABLE SI_OCM_PLU (
            PLUNumber INTEGER PRIMARY KEY AUTOINCREMENT,
            Description TEXT, ProductCode TEXT, Category TEXT,
            Species TEXT, PackSize REAL, ShelfLife INTEGER,
            Allergens TEXT, Active INTEGER DEFAULT 1, Updated TEXT
        );
    """)
    species_map = {
        'HAKE': 'hake', 'SEABASS': 'seabass', 'SALMON': 'salmon',
        'COD': 'cod', 'HADDOCK': 'haddock', 'MACKEREL': 'mackerel',
        'PRAWN': 'prawn', 'TUNA': 'tuna', 'PLAICE': 'plaice',
        'SOLE': 'sole', 'TROUT': 'trout', 'POLLOCK': 'pollock',
    }
    for prod in products:
        desc, pcode, pline = prod
        species = None
        for k, v in species_map.items():
            if k in desc.upper():
                species = v
                break
        c.execute(
            "INSERT INTO SI_OCM_PLU (Description, ProductCode, Category, Species, PackSize, ShelfLife, Allergens, Updated) VALUES (?,?,?,?,?,?,?,?)",
            (desc, pcode, 'fish', species, random.choice([130, 150, 170, 200, 280, 300, 400]),
             random.randint(4, 14), 'fish', now.strftime("%Y-%m-%d %H:%M:%S"))
        )

    # === SI_OCM_TOTALS (run aggregates) ===
    c.executescript("""
        DROP TABLE IF EXISTS SI_OCM_TOTALS;
        CREATE TABLE SI_OCM_TOTALS (
            RunNumber TEXT PRIMARY KEY, TotalPacks INTEGER,
            TotalWeight REAL, AvgWeight REAL, MinWeight REAL,
            MaxWeight REAL, StdDev REAL, Giveaway REAL,
            GiveawayPct REAL, RejectCount INTEGER,
            DowntimeMins INTEGER, Updated TEXT
        );
    """)
    for row in rows:
        run_num = row[0]
        # Realistic fish production: 80-400 packs per run
        packs = random.randint(80, 400)
        # Target weight matches product (130g-500g)
        target_wt = random.choice([130, 150, 170, 200, 240, 280, 300, 400, 500])
        # Avg weight is slightly above target (giveaway is overweight)
        avg_wt = target_wt + random.uniform(1, 8)
        total_kg = round(packs * avg_wt / 1000, 1)
        # Giveaway: realistic 0.5% to 4% of total weight
        giveaway_pct = round(random.uniform(0.5, 4.0), 1)
        giveaway_kg = round(total_kg * giveaway_pct / 100, 2)
        # Std dev realistic: 3-12g
        std_dev = round(random.uniform(3, 12), 1)
        # Rejects: 0-5% of packs
        reject_count = random.randint(0, max(1, int(packs * 0.05)))
        c.execute(
            "INSERT INTO SI_OCM_TOTALS VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_num, packs, total_kg,
             round(avg_wt, 1), round(avg_wt - std_dev * 2, 1), round(avg_wt + std_dev * 2, 1),
             std_dev, giveaway_kg, giveaway_pct,
             reject_count, random.randint(0, 20),
             row[10])  # Updated from RunNumber
        )

    conn.commit()
    conn.close()

    print(f"Mock ERP database created: {DB_PATH}")
    print(f"  RunNumber rows: {len(rows)}")
    print(f"  SI_OCM_TRANS rows: {trans_count}")
    print(f"  SI_OCM_PLU rows: {len(products)}")
    print(f"  SI_OCM_TOTALS rows: {len(rows)}")
    print(f"  Date range: {(now - timedelta(days=90)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")


if __name__ == "__main__":
    seed()
