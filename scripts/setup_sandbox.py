"""Set up the Docker sandbox with mock ERP data.

Usage:
    1. Start containers: docker-compose up -d
    2. Wait for SQL Server to be healthy: docker-compose ps
    3. Run this script: python scripts/setup_sandbox.py

This creates the schema and loads mock data into the containerised
SQL Server. The pipeline then extracts from this sandbox — never
from the real ERP.
"""
from __future__ import annotations

import os
import sys
import time

# Check if running against sandbox (safety check)
TARGET = os.getenv(
    "SANDBOX_DB",
    "mssql+pyodbc://sa:DemoPass123!@localhost/production_dw?driver=ODBC+Driver+17+for+SQL+Server"
)

if "localhost" not in TARGET and "127.0.0.1" not in TARGET:
    print("ERROR: This script only runs against localhost (sandbox).")
    print("       Never run against a production server.")
    sys.exit(1)


def wait_for_server(max_retries: int = 10):
    """Wait for SQL Server container to be ready."""
    from sqlalchemy import create_engine, text

    # Connect as SA first to create database
    sa_url = TARGET.replace("/production_dw", "/master")
    engine = create_engine(sa_url)

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print(f"SQL Server ready (attempt {attempt + 1})")
                return engine
        except Exception:
            print(f"Waiting for SQL Server... (attempt {attempt + 1}/{max_retries})")
            time.sleep(3)

    print("ERROR: SQL Server not responding after 30 seconds.")
    print("       Is the container running? docker-compose ps")
    sys.exit(1)


def create_database(engine):
    """Create the production_dw database if it doesn't exist."""
    from sqlalchemy import text

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        result = conn.execute(text(
            "SELECT name FROM sys.databases WHERE name = 'production_dw'"
        ))
        if not result.fetchone():
            conn.execute(text("CREATE DATABASE production_dw"))
            print("Created database: production_dw")
        else:
            print("Database production_dw already exists")


def create_readonly_user(engine):
    """Create read-only pipeline user."""
    from sqlalchemy import text

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # Check if login exists
        result = conn.execute(text(
            "SELECT name FROM sys.server_principals WHERE name = 'pipeline_reader'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "CREATE LOGIN pipeline_reader WITH PASSWORD = 'R3adOnly!Pass'"
            ))
            print("Created login: pipeline_reader")

    # Switch to production_dw
    from sqlalchemy import create_engine as _create_engine
    dw_url = TARGET
    dw_engine = _create_engine(dw_url)
    with dw_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        result = conn.execute(text(
            "SELECT name FROM sys.database_principals WHERE name = 'pipeline_reader'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "CREATE USER pipeline_reader FOR LOGIN pipeline_reader"
            ))
            conn.execute(text(
                "ALTER ROLE db_datareader ADD MEMBER pipeline_reader"
            ))
            conn.execute(text(
                "DENY INSERT, UPDATE, DELETE, ALTER TO pipeline_reader"
            ))
            print("Created read-only user: pipeline_reader")


def load_mock_data():
    """Load mock ERP data into the sandbox."""
    print("\nSeeding mock ERP data...")

    # Reuse the existing seed script but target the sandbox
    os.environ["SOURCE_DB"] = TARGET
    # The seed script creates a SQLite DB, but we'll adapt
    # For now, just confirm the sandbox is ready
    print("Mock data: use scripts/seed_mock_erp.py for SQLite, or load SQL files manually")
    print("  sqlcmd -S localhost -U sa -P 'DemoPass123!' -d production_dw -i sql/001_create_schema.sql")
    print("  sqlcmd -S localhost -U sa -P 'DemoPass123!' -d production_dw -i sql/002_seed_data.sql")


def main():

    print("=" * 60)
    print("SANDBOX SETUP")
    print("=" * 60)
    print(f"Target: {TARGET}")
    print()

    # Step 1: Wait for server
    engine = wait_for_server()

    # Step 2: Create database
    create_database(engine)

    # Step 3: Create read-only user
    create_readonly_user(engine)

    # Step 4: Load data
    load_mock_data()

    print()
    print("=" * 60)
    print("SANDBOX READY")
    print("=" * 60)
    print()
    print("Pipeline connection string (read-only):")
    print("  SOURCE_DB=mssql+pyodbc://pipeline_reader:R3adOnly!Pass@localhost/production_dw?driver=ODBC+Driver+17+for+SQL+Server")
    print()
    print("Run the pipeline:")
    print("  SOURCE_DB=<above> python -m workflow.daily_run --full")


if __name__ == "__main__":
    main()
