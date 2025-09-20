#!/usr/bin/env python3
"""Automated testing for config_deployment.py with input validation.

This script feeds test input to the config utility and validates
the resulting database contents match expected values.
"""

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


def create_test_input():
    """Create test input for config_deployment.py."""
    test_input = """2
web-server-01
192.168.1.100
root
/home/test/.ssh/id_rsa
22
y
2
db-server-01
192.168.1.200
dbadmin
/home/test/.ssh/db_key
2222
n
1
q
"""
    return test_input


def run_config_test(config_script, db_path, test_input):
    """Run config script with test input."""
    try:
        # Run the config script with input
        result = subprocess.run(
            ["python3", str(config_script), str(db_path)],
            input=test_input,
            text=True,
            capture_output=True,
            timeout=60,
        )

        return result.returncode == 0, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, "", "Configuration script timed out"
    except Exception as e:
        return False, "", str(e)


def validate_database_contents(db_path):
    """Validate that the database contains expected test data."""
    errors = []

    try:
        conn = sqlite3.connect(str(db_path))

        # Check hosts table
        cursor = conn.execute(
            "SELECT hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo FROM hosts ORDER BY hostname"
        )
        hosts = cursor.fetchall()

        expected_hosts = [
            (
                "db-server-01",
                "192.168.1.200",
                "dbadmin",
                "/home/test/.ssh/db_key",
                2222,
                0,
            ),
            ("web-server-01", "192.168.1.100", "root", "/home/test/.ssh/id_rsa", 22, 1),
        ]

        if hosts != expected_hosts:
            errors.append(f"Hosts mismatch. Expected: {expected_hosts}, Got: {hosts}")

        # Check global defaults (just verify they exist, don't test specific values since we didn't modify them)
        cursor = conn.execute(
            "SELECT max_snapshot_bytes, rpm_inventory, rpm_verify FROM global_defaults WHERE id = 1"
        )
        defaults = cursor.fetchone()

        if not defaults:
            errors.append("No global defaults found")
        else:
            # Just verify defaults exist and have reasonable values
            if defaults[0] is None or defaults[0] <= 0:
                errors.append(f"Invalid max_snapshot_bytes: {defaults[0]}")

            if defaults[1] not in (0, 1):
                errors.append(f"Invalid rpm_inventory value: {defaults[1]}")

            if defaults[2] not in (0, 1):
                errors.append(f"Invalid rpm_verify value: {defaults[2]}")

        conn.close()

    except sqlite3.Error as e:
        errors.append(f"Database error: {e}")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    return errors


def test_config_deployment_script(deployment_dir):
    """Test the config_deployment.py script with automated input."""
    print("\n🧪 Testing config_deployment.py automation...")

    config_script = deployment_dir / "scripts" / "config_deployment.py"
    init_script = deployment_dir / "scripts" / "init_deployment_db.py"

    if not config_script.exists():
        print("❌ config_deployment.py not found")
        return False

    if not init_script.exists():
        print("❌ init_deployment_db.py not found")
        return False

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        test_db = Path(f.name)

    try:
        # Initialize database
        print("  📊 Initializing test database...")
        init_result = subprocess.run(
            ["python3", str(init_script), str(test_db), "--with-defaults"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if init_result.returncode != 0:
            print(f"❌ Database initialization failed: {init_result.stderr}")
            return False

        print("  ✅ Database initialized")

        # Run config script with test input
        print("  🔧 Running config script with test input...")
        test_input = create_test_input()

        success, stdout, stderr = run_config_test(config_script, test_db, test_input)

        if not success:
            print(f"❌ Config script failed: {stderr}")
            print(f"stdout: {stdout}")
            return False

        print("  ✅ Config script completed")

        # Validate database contents
        print("  🔍 Validating database contents...")
        validation_errors = validate_database_contents(test_db)

        if validation_errors:
            print("❌ Database validation failed:")
            for error in validation_errors:
                print(f"    - {error}")
            return False

        print("  ✅ Database contents validated successfully")

        # Show what was actually created
        print("  📋 Created test data:")
        conn = sqlite3.connect(str(test_db))

        # Show hosts
        cursor = conn.execute(
            "SELECT hostname, ip, ssh_user FROM hosts ORDER BY hostname"
        )
        hosts = cursor.fetchall()
        for host in hosts:
            print(f"    Host: {host[0]} ({host[1]}) - user: {host[2]}")

        # Show global settings
        cursor = conn.execute(
            "SELECT max_snapshot_bytes, rpm_inventory, rpm_verify FROM global_defaults WHERE id = 1"
        )
        defaults = cursor.fetchone()
        if defaults:
            print(f"    Max snapshot bytes: {defaults[0]}")
            print(f"    RPM inventory: {'enabled' if defaults[1] else 'disabled'}")
            print(f"    RPM verify: {'enabled' if defaults[2] else 'disabled'}")
            print("    (Using default values - test didn't modify global settings)")

        conn.close()

        return True

    finally:
        # Clean up
        test_db.unlink(missing_ok=True)


def main():
    """Main test function."""
    if len(sys.argv) != 2:
        print("Usage: python test_config_automation.py DEPLOYMENT_DIR")
        sys.exit(1)

    deployment_dir = Path(sys.argv[1])

    if not deployment_dir.exists():
        print(f"❌ Deployment directory not found: {deployment_dir}")
        sys.exit(1)

    print("🧪 Testing Auditron Configuration Automation")
    print("=" * 60)

    if test_config_deployment_script(deployment_dir):
        print("\n✅ Configuration automation test passed!")
        print("🎯 The config script can be automated for testing and deployment")
        return 0
    else:
        print("\n❌ Configuration automation test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
