"""Test package for Auditron.

This package contains comprehensive unit and integration tests for the Auditron
auditing tool. Tests are organized by component and include:

- Unit tests for individual modules and functions
- Integration tests for complete workflows
- Mock-based tests for external dependencies
- Database consistency and schema tests
- SSH connection and command execution tests
- Strategy implementation tests
- Parser and utility function tests

Test Categories:
- unit: Fast tests with no external dependencies (default)
- integration: Tests that may require external resources
- slow: Tests that take more than a few seconds
- ssh: Tests that require SSH connectivity (usually mocked)
- db: Tests that require database operations

Usage:
    # Run all unit tests
    pytest -m "not integration"

    # Run only integration tests
    pytest -m integration

    # Run specific test file
    pytest tests/test_db.py

    # Run with coverage
    pytest --cov=utils --cov=strategies --cov=auditron
"""

__version__ = "1.0.0"
