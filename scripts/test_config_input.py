#!/usr/bin/env python3
"""Simple script to provide test input to config_deployment.py.

This script generates and pipes test configuration input to the
config utility for automated testing and demonstration purposes.

Usage:
    python scripts/test_config_input.py DATABASE_PATH
    
Example:
    python scripts/test_config_input.py test.db
"""

import subprocess
import sys
from pathlib import Path


def create_test_input():
    """Generate test input for config_deployment.py."""
    return """2
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


def main():
    """Run config_deployment.py with test input."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_config_input.py DATABASE_PATH")
        sys.exit(1)

    db_path = sys.argv[1]
    script_dir = Path(__file__).parent
    config_script = script_dir / "config_deployment.py"

    if not config_script.exists():
        print(f"❌ Config script not found: {config_script}")
        sys.exit(1)

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("Initialize it first with:")
        print(f"  python3 scripts/init_deployment_db.py {db_path} --with-defaults")
        sys.exit(1)

    print("🔧 Running config_deployment.py with test input...")
    print("📋 Adding test hosts and configuring settings...")

    test_input = create_test_input()

    try:
        result = subprocess.run(
            ["python3", str(config_script), db_path],
            input=test_input,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ Configuration completed successfully!")
        else:
            print("❌ Configuration failed!")
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print("❌ Configuration script timed out")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Configuration interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
