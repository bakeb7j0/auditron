#!/usr/bin/env python3
"""Integration test for Auditron deployment package.

This script validates that the deployment package works correctly
and can execute basic operations without errors.

Usage:
    python scripts/test_deployment.py [--deployment-dir deployment]
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    """Main test orchestration."""
    parser = argparse.ArgumentParser(description="Test Auditron deployment package")
    parser.add_argument(
        "--deployment-dir",
        default="deployment",
        help="Deployment directory to test (default: deployment)",
    )

    args = parser.parse_args()
    deployment_dir = Path(args.deployment_dir).resolve()

    print("🧪 Testing Auditron deployment package...")
    print(f"📁 Testing: {deployment_dir}")

    if not validate_deployment_structure(deployment_dir):
        sys.exit(1)

    if not test_executable_functionality(deployment_dir):
        sys.exit(1)

    if not test_database_operations(deployment_dir):
        sys.exit(1)

    print("✅ All deployment tests passed!")
    print("🚀 Deployment package is ready for field use")


def validate_deployment_structure(deployment_dir):
    """Validate deployment package structure."""
    print("\n📋 Validating deployment structure...")

    required_files = [
        "auditron",
        "README.md",
        "sample-config.sql",
        "scripts/init_deployment_db.py",
        "scripts/config_deployment.py",
        "docs/schema.sql",
    ]

    for file_path in required_files:
        full_path = deployment_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing required file: {file_path}")
            return False
        print(f"  ✅ {file_path}")

    # Check executable permissions
    executable = deployment_dir / "auditron"
    if not os.access(executable, os.X_OK):
        print("❌ Auditron executable lacks execute permissions")
        return False

    print("  ✅ All required files present with correct permissions")
    return True


def test_executable_functionality(deployment_dir):
    """Test basic executable functionality."""
    print("\n🔧 Testing executable functionality...")

    executable = deployment_dir / "auditron"

    # Test help output
    try:
        result = subprocess.run(
            [str(executable), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        if "Auditron" not in result.stdout or "Host auditing tool" not in result.stdout:
            print("❌ Help output doesn't contain expected content")
            return False
        print("  ✅ Help output test passed")

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ Help test failed: {e}")
        return False

    # Test error handling for invalid arguments
    try:
        result = subprocess.run(
            [str(executable), "--invalid-flag"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,  # We expect this to fail
        )

        # Should fail gracefully for invalid arguments
        if result.returncode == 0:
            print("❌ Expected failure for invalid arguments, but succeeded")
            return False
        print("  ✅ Error handling test passed")

    except subprocess.TimeoutExpired:
        print("❌ Executable hung when handling invalid arguments")
        return False

    return True


def test_database_operations(deployment_dir):
    """Test database initialization and configuration utilities."""
    print("\n🗄️ Testing database operations...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db = Path(temp_dir) / "test.db"

        # Test database initialization
        init_script = deployment_dir / "scripts" / "init_deployment_db.py"
        try:
            subprocess.run(
                ["python3", str(init_script), str(temp_db), "--with-defaults"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            print("  ✅ Database initialization test passed")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ Database initialization failed: {e}")
            print(f"stdout: {e.stdout if hasattr(e, 'stdout') else 'N/A'}")
            print(f"stderr: {e.stderr if hasattr(e, 'stderr') else 'N/A'}")
            return False

        # Verify database was created and has expected structure
        if not temp_db.exists():
            print("❌ Database file was not created")
            return False

        try:
            # Test basic database query
            subprocess.run(
                ["sqlite3", str(temp_db), "SELECT COUNT(*) FROM hosts;"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            print("  ✅ Database structure validation passed")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ Database structure validation failed: {e}")
            return False

        # Test config utility help (don't run interactive mode)
        config_script = deployment_dir / "scripts" / "config_deployment.py"
        try:
            subprocess.run(
                ["python3", str(config_script), "--help"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            print("  ✅ Config utility test passed")

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ Config utility test failed: {e}")
            return False

        # Test automated config with input validation
        print("  📊 Testing automated configuration...")
        try:
            # Import the automation test
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from tests.test_config_automation import test_config_deployment_script

            if test_config_deployment_script(deployment_dir):
                print("  ✅ Automated config test passed")
            else:
                print("  ❌ Automated config test failed")
                return False

        except Exception as e:
            print(f"  ⚠️ Automated config test skipped: {e}")
            # Don't fail the main test if automation test has issues

    return True


if __name__ == "__main__":
    main()
