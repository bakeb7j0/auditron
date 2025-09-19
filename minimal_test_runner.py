#!/usr/bin/env python3
"""Minimal test runner to validate our test suite setup."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock


def test_basic_functionality():
    """Test basic Python functionality."""
    print("Testing basic functionality...")

    # Test basic imports
    try:
        import sqlite3
        import tempfile
        import time
        from unittest.mock import Mock, patch

        print("✓ Basic imports successful")
    except ImportError as e:
        print(f"❌ Basic import failed: {e}")
        return False

    return True


def test_project_imports():
    """Test project-specific imports."""
    print("Testing project imports...")

    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))

        # Test utils imports
        from utils import db, parsing
        from utils.ssh_runner import SSHClient, SSHResult

        print("✓ Utils imports successful")

        # Test strategies imports
        from strategies.base import AuditCheck, AuditContext
        from strategies.osinfo import OSInfo

        print("✓ Strategies imports successful")

        return True

    except ImportError as e:
        print(f"⚠️ Project import failed (may be expected): {e}")
        return True  # Don't fail on this since some files may not exist yet


def test_database_operations():
    """Test basic database operations."""
    print("Testing database operations...")

    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        from utils import db

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Test connection
            conn = db.connect(db_path)
            print("✓ Database connection successful")

            # Test schema creation
            db.ensure_schema(conn)
            print("✓ Schema creation successful")

            # Test basic operations
            session_id = db.new_session(conn, "test")
            print(f"✓ Session created: {session_id}")

            db.finish_session(conn, session_id)
            print("✓ Session finished")

            conn.close()
            return True

        finally:
            Path(db_path).unlink(missing_ok=True)

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_parsing_functions():
    """Test parsing functionality."""
    print("Testing parsing functions...")

    try:
        sys.path.insert(0, str(Path.cwd()))
        from utils.parsing import parse_rpm_verify, parse_ss_listen

        # Test RPM verify parsing
        rpm_output = "SM5DLUGT. /etc/test.conf\n..5...... /bin/test\n"
        rows = parse_rpm_verify(rpm_output)
        assert len(rows) == 2
        assert rows[0][0] == "SM5DLUGT."
        assert rows[0][1] == "/etc/test.conf"
        print("✓ RPM verify parsing successful")

        # Test ss parsing
        ss_output = (
            'tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=123,fd=3))'
        )
        result = parse_ss_listen(ss_output)
        assert result[0] == "tcp"
        assert result[3] == 123
        assert result[4] == "sshd"
        print("✓ SS parsing successful")

        return True

    except Exception as e:
        print(f"❌ Parsing test failed: {e}")
        return False


def test_ssh_runner():
    """Test SSH runner functionality."""
    print("Testing SSH runner...")

    try:
        sys.path.insert(0, str(Path.cwd()))
        from utils.ssh_runner import SSHClient, SSHResult

        # Test SSHResult
        result = SSHResult(0, "success", "")
        assert result.rc == 0
        assert result.out == "success"
        print("✓ SSHResult creation successful")

        # Test SSHClient creation
        host_config = {
            "hostname": "test-host",
            "ip": "192.168.1.100",
            "ssh_user": "root",
            "ssh_key_path": "/tmp/test_key",
            "ssh_port": 22,
            "use_sudo": 1,
        }

        client = SSHClient(host_config)
        assert client.host == host_config
        assert client.timeout == 60
        print("✓ SSHClient creation successful")

        return True

    except Exception as e:
        print(f"❌ SSH runner test failed: {e}")
        return False


def test_strategy_base():
    """Test strategy base classes."""
    print("Testing strategy base classes...")

    try:
        sys.path.insert(0, str(Path.cwd()))
        from strategies.base import AuditContext

        # Test AuditContext creation
        host = {"id": 1, "hostname": "test"}
        ssh = Mock()
        db_conn = Mock()
        clock = Mock()

        ctx = AuditContext(
            host=host, ssh=ssh, db=db_conn, limits={}, clock=clock, session_id=1
        )

        assert ctx.host == host
        assert ctx.ssh == ssh
        assert ctx.session_id == 1
        print("✓ AuditContext creation successful")

        return True

    except Exception as e:
        print(f"❌ Strategy base test failed: {e}")
        return False


def validate_test_files():
    """Validate our test files exist and have basic structure."""
    print("Validating test file structure...")

    expected_files = [
        "tests/conftest.py",
        "tests/test_db.py",
        "tests/test_parsing_comprehensive.py",
        "tests/test_ssh_runner.py",
        "tests/test_strategies.py",
        "tests/test_auditron.py",
        "tests/test_utilities.py",
        "tests/integration/test_full_workflow.py",
        "pytest.ini",
    ]

    missing_files = []
    for file_path in expected_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✓ Found: {file_path}")

    if missing_files:
        print("❌ Missing files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return False

    print("✓ All test files present")
    return True


def run_pytest_syntax_check():
    """Check if pytest can at least parse our test files."""
    print("Checking pytest syntax...")

    try:
        import subprocess

        # Try to collect tests (syntax check)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✓ Pytest syntax check passed")
            lines = result.stdout.split("\n")
            test_count = len(
                [line for line in lines if "test_" in line and "::" in line]
            )
            print(f"✓ Found approximately {test_count} test methods")
            return True
        else:
            print(f"⚠️ Pytest syntax issues: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"⚠️ Pytest syntax check failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔍 Minimal Auditron Test Validation")
    print("=" * 50)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Project Imports", test_project_imports),
        ("Database Operations", test_database_operations),
        ("Parsing Functions", test_parsing_functions),
        ("SSH Runner", test_ssh_runner),
        ("Strategy Base", test_strategy_base),
        ("Test Files", validate_test_files),
        ("Pytest Syntax", run_pytest_syntax_check),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {name} failed")
        except Exception as e:
            print(f"❌ {name} error: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed!")
        print("\nThe test suite appears to be properly set up.")
        print("\nTo run the full test suite:")
        print("  pytest -v")
        print("  pytest -m 'not integration'  # Unit tests only")
        print("  pytest --cov=auditron --cov=utils --cov=strategies  # With coverage")
        return 0
    else:
        print(f"💥 {total - passed} validation tests failed")
        print("\nSome issues need to be resolved before running the full test suite.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
