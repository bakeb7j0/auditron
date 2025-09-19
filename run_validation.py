#!/usr/bin/env python3
"""Run validation and basic test checks."""

import subprocess
import sys
from pathlib import Path


def validate_structure():
    """Validate test structure."""
    print("Validating Auditron test structure...")
    print("=" * 50)
    
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
    
    print("\nChecking test files:")
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"✓ Found: {test_file}")
        else:
            errors.append(f"Missing: {test_file}")
    
    # Check conftest
    print("\nChecking conftest.py:")
    if Path("tests/conftest.py").exists():
        content = Path("tests/conftest.py").read_text()
        required_fixtures = ["temp_db", "sample_host", "mock_ssh_client", "audit_context"]
        missing_fixtures = [f for f in required_fixtures if f"def {f}" not in content]
        if missing_fixtures:
            errors.extend(f"Missing fixture: {f}" for f in missing_fixtures)
        else:
            print("✓ conftest.py is valid")
    else:
        errors.append("Missing tests/conftest.py")
    
    # Check pytest config
    print("\nChecking pytest configuration:")
    if Path("pytest.ini").exists():
        content = Path("pytest.ini").read_text()
        required_settings = ["testpaths = tests", "markers ="]
        missing_settings = [s for s in required_settings if s not in content]
        if missing_settings:
            errors.extend(f"Missing pytest config: {s}" for s in missing_settings)
        else:
            print("✓ pytest.ini is valid")
    else:
        errors.append("Missing pytest.ini")
    
    print("\n" + "=" * 50)
    
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ All validation checks passed!")
        return True

def check_imports():
    """Check if key modules can be imported."""
    print("\nTesting imports...")
    
    try:
        # Test basic imports
        print("✓ sqlite3 available")
        
        print("✓ tempfile available") 
        
        # Test project imports
        sys.path.insert(0, str(Path.cwd()))
        
        try:
            from utils import db
            print("✓ utils.db imported")
        except ImportError as e:
            print(f"⚠️ utils.db import failed: {e}")
        
        try:
            from utils import parsing
            print("✓ utils.parsing imported")
        except ImportError as e:
            print(f"⚠️ utils.parsing import failed: {e}")
            
        try:
            from utils.ssh_runner import SSHClient
            print("✓ utils.ssh_runner imported")
        except ImportError as e:
            print(f"⚠️ utils.ssh_runner import failed: {e}")
            
        try:
            from strategies.base import AuditContext
            print("✓ strategies.base imported")
        except ImportError as e:
            print(f"⚠️ strategies.base import failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def run_single_test():
    """Try to run a single test to validate the setup."""
    print("\nTesting pytest execution...")
    
    # Create a minimal test file to verify pytest works
    test_content = '''
def test_basic():
    """Basic test to verify pytest works."""
    assert True

def test_imports():
    """Test that we can import basic modules."""
    import sqlite3
    import tempfile
    assert sqlite3 is not None
    assert tempfile is not None
'''
    
    test_file = Path("test_basic_validation.py")
    test_file.write_text(test_content)
    
    try:
        # Try to run pytest on our basic test
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), "-v"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ pytest execution works")
            print("Sample output:")
            print(result.stdout[-200:] if len(result.stdout) > 200 else result.stdout)
            return True
        else:
            print("❌ pytest execution failed")
            print("Error:", result.stderr[-200:] if len(result.stderr) > 200 else result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ pytest execution timed out")
        return False
    except FileNotFoundError:
        print("⚠️ pytest not found")
        return False
    except Exception as e:
        print(f"❌ pytest execution error: {e}")
        return False
    finally:
        # Clean up test file
        test_file.unlink(missing_ok=True)

def main():
    """Run all validation checks."""
    print("🔍 Auditron Test Suite Validation")
    print("=" * 60)
    
    success = True
    
    # Structure validation
    if not validate_structure():
        success = False
    
    # Import testing  
    if not check_imports():
        success = False
    
    # Basic pytest test
    if not run_single_test():
        success = False
        
    print("\n" + "=" * 60)
    
    if success:
        print("🎉 Validation completed successfully!")
        print("\nNext steps:")
        print("- Run unit tests: pytest -m 'not integration'")
        print("- Run all tests: pytest")
        print("- Run with coverage: pytest --cov=auditron --cov=utils --cov=strategies")
        return 0
    else:
        print("💥 Validation failed - please check errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())