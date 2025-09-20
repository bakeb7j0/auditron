#!/usr/bin/env python3
"""Deployment-friendly configuration utility for Auditron.

This script provides interactive configuration management for Auditron
databases, accepting the database path as a parameter for field deployment.

Usage:
    python scripts/config_deployment.py DATABASE_PATH
    
Example:
    python scripts/config_deployment.py workspace/auditron.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def connect_db(db_path):
    """Connect to database and enable foreign keys."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def ensure_schema(conn, db_path):
    """Ensure database has proper schema."""
    # Find schema file relative to this script
    script_dir = Path(__file__).parent
    schema_path = script_dir.parent / "docs" / "schema.sql"

    if not schema_path.exists():
        print(f"⚠️  Schema file not found at {schema_path}")
        print("Database may not be properly initialized.")
        return

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    except sqlite3.Error as e:
        print(f"⚠️  Schema update failed: {e}")


def list_hosts(conn):
    """Display configured hosts."""
    try:
        cursor = conn.execute(
            """
            SELECT id, hostname, ip, ssh_user, ssh_port, use_sudo 
            FROM hosts ORDER BY id
        """
        )
        hosts = cursor.fetchall()

        print("\n📋 Configured Hosts:")
        if not hosts:
            print("  No hosts configured.")
            return

        for row in hosts:
            sudo_text = "yes" if row[5] else "no"
            print(
                f"  [{row[0]}] {row[1]} ({row[2]}) user={row[3]} port={row[4]} sudo={sudo_text}"
            )

    except sqlite3.Error as e:
        print(f"❌ Error listing hosts: {e}")


def add_host(conn):
    """Add a new host interactively."""
    print("\n➕ Adding New Host")

    try:
        hostname = input("Hostname: ").strip()
        if not hostname:
            print("❌ Hostname cannot be empty")
            return

        ip = input("IP Address: ").strip()
        if not ip:
            print("❌ IP address cannot be empty")
            return

        user = input("SSH User [root]: ").strip() or "root"
        key = input("SSH Key Path (optional): ").strip() or None

        port_input = input("SSH Port [22]: ").strip()
        try:
            port = int(port_input) if port_input else 22
        except ValueError:
            print("❌ Invalid port number, using default 22")
            port = 22

        sudo_input = input("Use sudo? [y/N]: ").strip().lower()
        use_sudo = 1 if sudo_input in ("y", "yes") else 0

        # Insert host
        conn.execute(
            """
            INSERT INTO hosts (hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) 
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (hostname, ip, user, key, port, use_sudo),
        )
        conn.commit()

        print(f"✅ Host '{hostname}' added successfully")

    except sqlite3.Error as e:
        print(f"❌ Error adding host: {e}")
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled")


def remove_host(conn):
    """Remove a host by ID."""
    list_hosts(conn)

    try:
        host_id = input("\nHost ID to remove: ").strip()
        if not host_id:
            return

        host_id = int(host_id)

        # Check if host exists
        cursor = conn.execute("SELECT hostname FROM hosts WHERE id = ?", (host_id,))
        host = cursor.fetchone()

        if not host:
            print(f"❌ Host with ID {host_id} not found")
            return

        # Confirm deletion
        confirm = input(f"Delete host '{host[0]}'? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("⚠️  Deletion cancelled")
            return

        conn.execute("DELETE FROM hosts WHERE id = ?", (host_id,))
        conn.commit()
        print(f"✅ Host '{host[0]}' removed successfully")

    except ValueError:
        print("❌ Invalid host ID")
    except sqlite3.Error as e:
        print(f"❌ Error removing host: {e}")
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled")


def manage_global_defaults(conn):
    """Manage global default settings."""
    print("\n⚙️  Global Default Settings")

    # Ensure global defaults exist
    cursor = conn.execute("SELECT 1 FROM global_defaults WHERE id = 1")
    if not cursor.fetchone():
        conn.execute("INSERT INTO global_defaults (id) VALUES (1)")
        conn.commit()
        print("✅ Created global defaults entry")

    # Get column info
    cursor = conn.execute("PRAGMA table_info(global_defaults)")
    columns = [col[1] for col in cursor.fetchall()]

    # Separate flags from other settings
    flag_columns = [
        col
        for col in columns[1:]
        if col not in ("max_snapshot_bytes", "gzip_snapshots", "command_timeout_sec")
    ]

    while True:
        # Get current values
        cursor = conn.execute("SELECT * FROM global_defaults WHERE id = 1")
        row = cursor.fetchone()
        values = dict(zip(columns, row))

        print("\n📊 Current Settings:")
        print(f"  Max Snapshot Bytes: {values.get('max_snapshot_bytes', 'NULL')}")
        print(f"  Gzip Snapshots: {values.get('gzip_snapshots', 'NULL')}")
        print(f"  Command Timeout: {values.get('command_timeout_sec', 'NULL')} seconds")
        print()

        print("🎛️  Audit Strategy Flags (1=enabled, 0=disabled):")
        for i, flag in enumerate(flag_columns, 1):
            status = values.get(flag, 0)
            print(f"  {i}. {flag}: {status}")

        print("\n  s) Set limits (bytes/compression/timeout)")
        print("  q) Back to main menu")

        choice = input("\n> ").strip().lower()

        if choice == "q":
            break
        elif choice == "s":
            set_limits(conn, values)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(flag_columns):
                    flag = flag_columns[idx]
                    current_value = values.get(flag, 0)
                    new_value = 0 if current_value == 1 else 1

                    conn.execute(
                        f"UPDATE global_defaults SET {flag} = ? WHERE id = 1",
                        (new_value,),
                    )
                    conn.commit()
                    print(f"✅ {flag} set to {new_value}")
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Invalid choice")
            except sqlite3.Error as e:
                print(f"❌ Database error: {e}")


def set_limits(conn, current_values):
    """Set limit values interactively."""
    print("\n📏 Setting Limits")

    try:
        # Max snapshot bytes
        current_bytes = current_values.get("max_snapshot_bytes", 1048576)
        bytes_input = input(f"Max Snapshot Bytes [{current_bytes}]: ").strip()
        if bytes_input:
            try:
                max_bytes = int(bytes_input)
                conn.execute(
                    "UPDATE global_defaults SET max_snapshot_bytes = ? WHERE id = 1",
                    (max_bytes,),
                )
            except ValueError:
                print("❌ Invalid number for max bytes")

        # Gzip snapshots
        current_gzip = current_values.get("gzip_snapshots", 1)
        gzip_input = input(f"Gzip Snapshots (0/1) [{current_gzip}]: ").strip()
        if gzip_input:
            try:
                gzip_value = int(gzip_input)
                if gzip_value in (0, 1):
                    conn.execute(
                        "UPDATE global_defaults SET gzip_snapshots = ? WHERE id = 1",
                        (gzip_value,),
                    )
                else:
                    print("❌ Gzip value must be 0 or 1")
            except ValueError:
                print("❌ Invalid number for gzip setting")

        # Command timeout
        current_timeout = current_values.get("command_timeout_sec", 60)
        timeout_input = input(f"Command Timeout Seconds [{current_timeout}]: ").strip()
        if timeout_input:
            try:
                timeout_value = int(timeout_input)
                conn.execute(
                    "UPDATE global_defaults SET command_timeout_sec = ? WHERE id = 1",
                    (timeout_value,),
                )
            except ValueError:
                print("❌ Invalid number for timeout")

        conn.commit()
        print("✅ Limits updated successfully")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")


def main():
    """Main interactive configuration loop."""
    parser = argparse.ArgumentParser(
        description="Interactive configuration utility for Auditron deployment"
    )
    parser.add_argument(
        "database_path", help="Path to the Auditron SQLite database file"
    )

    args = parser.parse_args()

    db_path = Path(args.database_path)

    if not db_path.exists():
        print(f"❌ Database file not found: {db_path}")
        print("Initialize it first with:")
        print(f"  python3 scripts/init_deployment_db.py {db_path} --with-defaults")
        sys.exit(1)

    try:
        conn = connect_db(db_path)
        ensure_schema(conn, db_path)

        print("🔧 Auditron Configuration Utility")
        print(f"📁 Database: {db_path}")

        while True:
            print(f"\n{'='*50}")
            print("📋 Main Menu:")
            print("  1) List hosts")
            print("  2) Add host")
            print("  3) Remove host")
            print("  4) Global default settings")
            print("  q) Quit")

            choice = input("\n> ").strip().lower()

            if choice == "1":
                list_hosts(conn)
            elif choice == "2":
                add_host(conn)
            elif choice == "3":
                remove_host(conn)
            elif choice == "4":
                manage_global_defaults(conn)
            elif choice == "q":
                break
            else:
                print("❌ Invalid choice")

        conn.close()
        print("\n👋 Configuration utility exited")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Configuration utility interrupted")
        sys.exit(0)


if __name__ == "__main__":
    main()
