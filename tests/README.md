# Auditron Test Suite

This directory contains the comprehensive test suite for Auditron - **111+ tests** providing enterprise-grade quality assurance with **92% coverage** and **Pylint 9.17/10** score.

## Test Organization

### Unit Tests
- `test_db.py` - Database utilities and operations
- `test_parsing_comprehensive.py` - Command output parsers  
- `test_ssh_runner.py` - SSH client and command execution
- `test_strategies.py` - Audit strategy implementations
- `test_auditron.py` - Main orchestrator and CLI
- `test_utilities.py` - Utility functions and helpers
- `test_parsers.py` - Legacy parser tests (kept for compatibility)

### Integration Tests
- `integration/test_full_workflow.py` - End-to-end workflow tests

### Test Infrastructure
- `conftest.py` - Shared pytest fixtures
- `test_runner.py` - Custom test runner with coverage
- `__init__.py` - Package initialization and documentation

## Test Categories (Markers)

Tests are categorized using pytest markers:

- `unit` - Fast tests with no external dependencies (default)
- `integration` - Tests that may require external resources
- `slow` - Tests that take more than a few seconds
- `ssh` - Tests that require SSH connectivity (usually mocked)
- `db` - Tests that require database operations

## Running Tests

### Prerequisites

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Basic Usage

```bash
# Run all unit tests (fast, no external dependencies)
pytest -m "not integration"

# Run all tests including integration tests
pytest

# Run specific test file
pytest tests/test_db.py

# Run specific test class
pytest tests/test_db.py::TestDatabaseConnection

# Run specific test method
pytest tests/test_db.py::TestDatabaseConnection::test_connect_creates_connection
```

### Coverage Reports

```bash
# Run with coverage reporting
pytest --cov=auditron --cov=utils --cov=strategies

# Generate HTML coverage report
pytest --cov=auditron --cov=utils --cov=strategies --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Filtering

```bash
# Run only database tests
pytest -m db

# Run only SSH-related tests  
pytest -m ssh

# Run only slow tests
pytest -m slow

# Run everything except slow tests
pytest -m "not slow"

# Combine markers
pytest -m "unit and db"
```

### Verbose Output

```bash
# Verbose output with test names
pytest -v

# Show local variables on failure
pytest -l

# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

### Custom Test Runner

Use the custom test runner for a complete test suite:

```bash
python tests/test_runner.py
```

This runs:
1. Unit tests with coverage
2. Linting checks (ruff, flake8)
3. Type checking (pyright, if available)
4. Integration tests

## Test Structure

### Fixtures (conftest.py)

Key fixtures available to all tests:

- `temp_db` - Temporary SQLite database with schema
- `sample_host` - Sample host configuration
- `mock_ssh_client` - Mock SSH client returning success
- `mock_failing_ssh_client` - Mock SSH client returning failures  
- `audit_context` - Complete AuditContext for strategy testing
- `populated_db` - Database with sample hosts and sessions
- Sample command outputs: `rpm_verify_output`, `ss_listen_output`, etc.

### Test Data

Test data is provided through fixtures to ensure consistency:

```python
def test_example(sample_host, audit_context, rpm_verify_output):
    # Use fixtures in your tests
    assert sample_host["hostname"] == "test-host"
    assert audit_context.host == sample_host
    assert "SM5DLUGT" in rpm_verify_output
```

### Mocking Strategy

Tests extensively use mocking to isolate components:

- SSH operations are mocked to avoid network dependencies
- Database operations use temporary in-memory databases
- External commands are mocked with realistic outputs
- Time/clock operations are mocked for deterministic results

## Writing New Tests

### Test File Naming

- Unit tests: `test_<module_name>.py`
- Integration tests: `integration/test_<feature>.py`

### Test Class Organization

```python
class TestComponentName:
    """Test ComponentName functionality."""
    
    def test_basic_functionality(self):
        """Test basic functionality works."""
        pass
        
    def test_error_handling(self):
        """Test error conditions are handled."""
        pass
        
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        pass
```

### Using Fixtures

```python
def test_with_database(temp_db, sample_host):
    """Test using database and host fixtures."""
    # temp_db is ready-to-use SQLite connection
    # sample_host is a valid host configuration dict
    pass

def test_with_audit_context(audit_context):
    """Test using complete audit context."""
    # audit_context has host, ssh, db, session_id ready
    pass
```

### Marking Tests

```python
import pytest

@pytest.mark.unit
def test_unit_functionality():
    """Fast unit test."""
    pass

@pytest.mark.integration  
def test_integration_workflow():
    """Integration test requiring external resources."""
    pass

@pytest.mark.slow
def test_time_consuming_operation():
    """Test that takes a while to run."""
    pass
```

### Testing Exceptions

```python
def test_error_conditions():
    """Test error handling."""
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_should_fail("bad input")
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"), 
    ("test3", "result3"),
])
def test_multiple_inputs(input, expected):
    """Test with multiple input/output pairs."""
    assert process(input) == expected
```

## Test Coverage Goals

Target coverage levels:
- Overall: ≥75% (currently 92%)
- Core modules (auditron.py, utils/, strategies/): ≥90%
- Critical functions (database, SSH, parsing): ≥95%

## Continuous Integration

Tests run automatically in GitHub Actions with comprehensive quality gates:

1. **Lint Job**: ruff, black, isort, flake8, pylint (9.17/10), pyright
2. **Unit Tests**: Python 3.10, 3.11, 3.12 with 75%+ coverage requirement
3. **Integration Tests**: End-to-end workflow validation
4. **Quality Gates**: All linters passing, coverage thresholds enforced

Current Status: **✅ All 111 tests passing, 0 warnings, production ready**

See `.github/workflows/ci.yml` for complete pipeline details.

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/path/to/auditron:$PYTHONPATH
pytest tests/
```

**Database Lock Errors**:
```bash
# Clean up any hanging database connections
rm -f test_*.db auditron_test.db
```

**SSH Mock Issues**:
```bash
# Check that SSH mocks are properly configured
pytest tests/test_ssh_runner.py -v
```

**Coverage Issues**:
```bash
# Check which lines are not covered
pytest --cov=auditron --cov-report=term-missing
```

## Contributing

When adding new functionality:

1. Write tests first (TDD approach)
2. Ensure >90% coverage for new code
3. Add integration tests for new strategies
4. Update fixtures if needed
5. Run full test suite before committing

```bash
# Validate everything works
python validate_tests.py
python tests/test_runner.py
```