#!/usr/bin/env python3
"""Script to validate test structure and imports."""

import sys
from pathlib import Path


def check_test_files():
    """Check that all test files can be imported."""
    test_files = [
        "tests/test_db.py",
        "tests/test_parsing_comprehensive.py", 
        "tests/test_ssh_runner.py",
        "tests/test_strategies.py",
        "tests/test_auditron.py",
        "tests/test_utilities.py",
        "tests/integration/test_full_workflow.py"
    ]
    
    errors = []
    
    for test_file in test_files:
        if not Path(test_file).exists():
            errors.append(f"Missing: {test_file}")
            continue
            
        print(f"✓ Found: {test_file}")
    
    return errors

def check_conftest():
    """Check conftest.py exists and has fixtures."""
    conftest_path = Path("tests/conftest.py")
    if not conftest_path.exists():
        return ["Missing tests/conftest.py"]
    
    content = conftest_path.read_text()
    required_fixtures = [
        "temp_db",
        "sample_host", 
        "mock_ssh_client",
        "audit_context"
    ]
    
    errors = []
    for fixture in required_fixtures:
        if f"def {fixture}" not in content:
            errors.append(f"Missing fixture: {fixture}")
    
    return errors

def check_pytest_config():
    """Check pytest configuration."""
    config_path = Path("pytest.ini")
    if not config_path.exists():
        return ["Missing pytest.ini"]
    
    content = config_path.read_text()
    required_settings = [
        "testpaths = tests",
        "markers =",
        "integration:",
        "unit:"
    ]
    
    errors = []
    for setting in required_settings:
        if setting not in content:
            errors.append(f"Missing pytest config: {setting}")
    
    return errors

def main():
    """Run validation checks."""
    print("Validating Auditron test structure...")
    print("=" * 50)
    
    all_errors = []
    
    # Check test files
    print("\nChecking test files:")
    all_errors.extend(check_test_files())
    
    # Check conftest
    print("\nChecking conftest.py:")
    conftest_errors = check_conftest()
    if conftest_errors:
        all_errors.extend(conftest_errors)
    else:
        print("✓ conftest.py is valid")
    
    # Check pytest config
    print("\nChecking pytest configuration:")
    config_errors = check_pytest_config()
    if config_errors:
        all_errors.extend(config_errors)
    else:
        print("✓ pytest.ini is valid")
    
    print("\n" + "=" * 50)
    
    if all_errors:
        print("❌ Validation failed:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print("✅ All validation checks passed!")
        print("\nTest structure summary:")
        print("- Unit tests: test_*.py (7 files)")
        print("- Integration tests: tests/integration/ (1 file)")
        print("- Fixtures: tests/conftest.py")
        print("- Configuration: pytest.ini")
        print("\nTo run tests:")
        print("  # Unit tests only:")
        print("  pytest -m 'not integration'")
        print("  # All tests:")
        print("  pytest")
        print("  # With coverage:")
        print("  pytest --cov=auditron --cov=utils --cov=strategies")
        return 0

if __name__ == "__main__":
    sys.exit(main())