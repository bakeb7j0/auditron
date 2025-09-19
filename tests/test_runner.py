#!/usr/bin/env python3
"""Test runner for Auditron with coverage reporting."""

import subprocess
import sys
from pathlib import Path


def run_unit_tests():
    """Run unit tests with coverage."""
    print("Running unit tests...")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "--maxfail=5",
        "-m",
        "not integration",
        "tests/",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "--maxfail=3",
        "-m",
        "integration",
        "tests/integration/",
    ]

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_linting():
    """Run linting checks."""
    print("Running linting checks...")

    # Run ruff
    ruff_cmd = ["ruff", "check", ".", "--output-format=text"]
    ruff_result = subprocess.run(ruff_cmd, cwd=Path(__file__).parent.parent)

    # Run flake8
    flake8_cmd = ["flake8", "auditron.py", "utils/", "strategies/", "tests/"]
    flake8_result = subprocess.run(flake8_cmd, cwd=Path(__file__).parent.parent)

    return ruff_result.returncode == 0 and flake8_result.returncode == 0


def run_type_checking():
    """Run type checking with pyright."""
    print("Running type checking...")

    cmd = ["pyright"]
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def main():
    """Run complete test suite."""
    print("=" * 60)
    print("Auditron Test Suite")
    print("=" * 60)

    all_passed = True

    # Run unit tests
    if not run_unit_tests():
        print("❌ Unit tests failed")
        all_passed = False
    else:
        print("✅ Unit tests passed")

    print()

    # Run linting
    if not run_linting():
        print("❌ Linting checks failed")
        all_passed = False
    else:
        print("✅ Linting checks passed")

    print()

    # Run type checking (optional)
    try:
        if not run_type_checking():
            print("⚠️  Type checking failed (non-critical)")
        else:
            print("✅ Type checking passed")
    except FileNotFoundError:
        print("⚠️  Type checking skipped (pyright not found)")

    print()

    # Run integration tests
    if not run_integration_tests():
        print("❌ Integration tests failed")
        all_passed = False
    else:
        print("✅ Integration tests passed")

    print()
    print("=" * 60)

    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
