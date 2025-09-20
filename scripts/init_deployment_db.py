#!/usr/bin/env python3
"""Initialize Auditron database for deployment.

This script creates a new SQLite database with the proper schema
and default configuration for field deployment.

Usage:
    python scripts/init_deployment_db.py DATABASE_PATH [--with-defaults]
    
Example:
    python scripts/init_deployment_db.py workspace/auditron.db --with-defaults
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def main():
    """Main database initialization function."""
    parser = argparse.ArgumentParser(
        description="Initialize Auditron database for deployment"
    )
    parser.add_argument(
        "database_path", help="Path to the SQLite database file to create"
    )
    parser.add_argument(
        "--with-defaults",
        action="store_true",
        help="Initialize with default global settings",
    )

    args = parser.parse_args()

    db_path = Path(args.database_path)

    # Create parent directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🗄️ Initializing database: {db_path}")

    try:
        # Initialize database with schema
        conn = initialize_database(db_path)

        # Add default configuration if requested
        if args.with_defaults:
            initialize_defaults(conn)

        conn.close()
        print("✅ Database initialization completed successfully!")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


def initialize_database(db_path):
    """Create database with proper schema."""

    # Find schema file relative to this script
    script_dir = Path(__file__).parent
    schema_path = script_dir.parent / "docs" / "schema.sql"

    if not schema_path.exists():
        # Try deployment structure
        schema_path = script_dir.parent / "docs" / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

    # Create database connection
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON;")

    # Load and execute schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()

    print(f"  ✅ Schema loaded from {schema_path}")

    return conn


def initialize_defaults(conn):
    """Initialize global defaults table."""

    # Check if defaults already exist
    cursor = conn.execute("SELECT 1 FROM global_defaults WHERE id = 1")
    if cursor.fetchone():
        print("  ⚠️  Global defaults already exist, skipping")
        return

    # Insert default global settings (all checks enabled)
    conn.execute(
        """
        INSERT INTO global_defaults (
            id, max_snapshot_bytes, rpm_inventory, rpm_verify, 
            processes, sockets, osinfo, routes
        ) VALUES (1, 1048576, 1, 1, 1, 1, 1, 1)
    """
    )

    conn.commit()
    print("  ✅ Global defaults initialized (all checks enabled)")


if __name__ == "__main__":
    main()
