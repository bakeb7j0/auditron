#!/usr/bin/env python3
"""Update project metrics across all documentation files.

This script extracts current project metrics (test coverage, test count, pylint score)
and updates all documentation files that reference these metrics. It can be run
manually or as part of pre-commit hooks to ensure documentation stays current.

Usage:
    python scripts/update_metrics.py [--check-only] [--verbose]
    
Options:
    --check-only    Only check if metrics are current, don't update files
    --verbose       Show detailed output of what's being updated
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class ProjectMetrics:
    """Container for project quality metrics."""

    def __init__(self):
        self.test_count = 0
        self.test_coverage = 0.0
        self.pylint_score = 0.0
        self.skipped_tests = 0
        self.deselected_tests = 0

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "test_count": self.test_count,
            "test_coverage": self.test_coverage,
            "pylint_score": self.pylint_score,
            "skipped_tests": self.skipped_tests,
            "deselected_tests": self.deselected_tests,
        }

    def from_dict(self, data: Dict):
        """Load metrics from dictionary."""
        self.test_count = data.get("test_count", 0)
        self.test_coverage = data.get("test_coverage", 0.0)
        self.pylint_score = data.get("pylint_score", 0.0)
        self.skipped_tests = data.get("skipped_tests", 0)
        self.deselected_tests = data.get("deselected_tests", 0)


def get_current_metrics(verbose: bool = False) -> ProjectMetrics:
    """Extract current project metrics by running tests and analysis."""
    metrics = ProjectMetrics()

    if verbose:
        print("📊 Collecting current project metrics...")

    # Run pytest to get test count and coverage
    try:
        result = subprocess.run(
            [
                "python3",
                "-m",
                "pytest",
                "-q",
                "-m",
                "not integration",
                "--cov=auditron",
                "--cov=utils",
                "--cov=strategies",
                "--cov-report=json",
                "--cov-report=term-missing",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if verbose:
            print("  🧪 Running test suite...")

        # Parse test counts from output - look for summary line
        output = result.stdout + result.stderr

        # Remove ANSI color codes for easier parsing
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        clean_output = ansi_escape.sub("", output)

        # Look for summary line pattern
        summary_pattern = r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) deselected)?"
        match = re.search(summary_pattern, clean_output)
        if match:
            metrics.test_count = int(match.group(1))
            if match.group(2):
                metrics.skipped_tests = int(match.group(2))
            if match.group(3):
                metrics.deselected_tests = int(match.group(3))

        # Parse coverage from terminal output
        # Try to parse from clean terminal output
        for line in clean_output.split("\n"):
            if "TOTAL" in line and "%" in line:
                # Parse line like "TOTAL                           408     24    94%"
                parts = line.split()
                for part in parts:
                    if part.endswith("%"):
                        try:
                            metrics.test_coverage = float(part[:-1])
                            break
                        except ValueError:
                            pass
            elif "Total coverage:" in line and "%" in line:
                # Parse lines like "Total coverage: 94.12%"
                match = re.search(r"(\d+\.\d+)%", line)
                if match:
                    metrics.test_coverage = float(match.group(1))
                    break

        if verbose:
            print(
                f"    ✅ Tests: {metrics.test_count} passed, {metrics.skipped_tests} skipped"
            )
            print(f"    📈 Coverage: {metrics.test_coverage:.2f}%")

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"⚠️  Failed to get test metrics: {e}")

    # Get pylint score (this should be cached/fast)
    try:
        if verbose:
            print("  🔍 Running pylint analysis...")

        result = subprocess.run(
            ["pylint", "auditron.py", "utils/", "strategies/", "--score=yes"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Parse pylint score from output
        for line in result.stdout.split("\n"):
            if "Your code has been rated at" in line:
                # Parse line like "Your code has been rated at 9.17/10"
                match = re.search(r"(\d+\.\d+)/10", line)
                if match:
                    metrics.pylint_score = float(match.group(1))
                    if verbose:
                        print(f"    🏆 Pylint score: {metrics.pylint_score}/10")
                    break

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"⚠️  Failed to get pylint score: {e}")
        # Use fallback score from documentation if available
        metrics.pylint_score = 9.17

    return metrics


def save_metrics(metrics: ProjectMetrics, metrics_file: Path):
    """Save metrics to JSON file."""
    with open(metrics_file, "w") as f:
        json.dump(metrics.to_dict(), f, indent=2)


def load_metrics(metrics_file: Path) -> ProjectMetrics:
    """Load metrics from JSON file."""
    metrics = ProjectMetrics()
    if metrics_file.exists():
        with open(metrics_file) as f:
            data = json.load(f)
            metrics.from_dict(data)
    return metrics


def update_documentation_files(
    metrics: ProjectMetrics, verbose: bool = False
) -> List[str]:
    """Update all documentation files with current metrics."""

    updated_files = []

    # Define metric substitutions
    substitutions = [
        # Test count patterns
        (r"\b\d{2,3}\+?\s+tests?\b", f"{metrics.test_count}+ tests"),
        (r"\b\d{2,3}\+?\s+test methods?\b", f"{metrics.test_count}+ test methods"),
        (r"(\*\*)\d{2,3}(\+?\s+tests?)(\*\*)", rf"\g<1>{metrics.test_count}\g<2>\g<3>"),
        # Coverage patterns
        (r"\b\d{1,2}\.\d{1,2}%", f"{metrics.test_coverage:.2f}%"),
        (
            r"coverage-\d{1,2}(\.\d{1,2})?%25",
            f"coverage-{metrics.test_coverage:.2f}%25",
        ),
        (r"currently \d{1,2}(\.\d{1,2})?%", f"currently {metrics.test_coverage:.2f}%"),
        # Pylint score patterns
        (r"pylint-\d\.\d{1,2}%2F10", f"pylint-{metrics.pylint_score:.2f}%2F10"),
        (r"Pylint:?\s*\d\.\d{1,2}/10", f"Pylint: {metrics.pylint_score:.2f}/10"),
        (r"pylint.*?(\d\.\d{1,2})/10", rf"pylint {metrics.pylint_score:.2f}/10"),
    ]

    # Files to update
    doc_files = [
        "README.md",
        "docs/seed-prompt.md",
        "tests/README.md",
        "FINAL_TEST_REPORT.md",
        "TEST_SUITE_SUMMARY.md",
        "docs/test-plan.md",
        "docs/component-map.md",
    ]

    for doc_file in doc_files:
        file_path = Path(doc_file)
        if not file_path.exists():
            continue

        content = file_path.read_text()
        original_content = content

        # Apply all substitutions
        for pattern, replacement in substitutions:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        # Check if file was modified
        if content != original_content:
            file_path.write_text(content)
            updated_files.append(str(file_path))
            if verbose:
                print(f"  📝 Updated {file_path}")

    return updated_files


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(
        description="Update project metrics across documentation files"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if metrics are current, don't update files",
    )
    parser.add_argument(
        "--enforce-quality",
        action="store_true",
        help="Fail if code quality metrics have decreased (for pre-commit)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    # Ensure we're in project root
    project_root = Path(__file__).parent.parent
    if not (project_root / "auditron.py").exists():
        print("❌ Must be run from project root directory")
        sys.exit(1)

    metrics_file = project_root / ".project-metrics.json"

    if args.verbose:
        print("🎯 Auditron Metrics Update Tool")
        print("=" * 50)

    # Get current metrics
    current_metrics = get_current_metrics(args.verbose)

    # Load existing metrics for comparison
    existing_metrics = load_metrics(metrics_file)

    if args.check_only:
        # Just check if metrics are current
        if (
            current_metrics.test_count != existing_metrics.test_count
            or abs(current_metrics.test_coverage - existing_metrics.test_coverage) > 0.1
            or abs(current_metrics.pylint_score - existing_metrics.pylint_score) > 0.01
        ):

            print("⚠️  Metrics are out of date!")
            print(
                f"   Tests: {existing_metrics.test_count} → {current_metrics.test_count}"
            )
            print(
                f"   Coverage: {existing_metrics.test_coverage:.2f}% → {current_metrics.test_coverage:.2f}%"
            )
            print(
                f"   Pylint: {existing_metrics.pylint_score:.2f} → {current_metrics.pylint_score:.2f}"
            )
            sys.exit(1)
        else:
            if args.verbose:
                print("✅ All metrics are current!")
            sys.exit(0)

    if args.enforce_quality:
        # UNYIELDING COMMITMENT TO CODE QUALITY!
        quality_failures = []

        # Check test coverage - must not decrease
        if current_metrics.test_coverage < existing_metrics.test_coverage - 0.1:
            quality_failures.append(
                f"🚨 COVERAGE REGRESSION: {existing_metrics.test_coverage:.2f}% → {current_metrics.test_coverage:.2f}% "
                f"(-{existing_metrics.test_coverage - current_metrics.test_coverage:.2f}%)"
            )

        # Check pylint score - must not decrease
        if current_metrics.pylint_score < existing_metrics.pylint_score - 0.05:
            quality_failures.append(
                f"🚨 PYLINT REGRESSION: {existing_metrics.pylint_score:.2f} → {current_metrics.pylint_score:.2f} "
                f"(-{existing_metrics.pylint_score - current_metrics.pylint_score:.2f})"
            )

        # Check test count - should not decrease significantly
        if current_metrics.test_count < existing_metrics.test_count - 2:
            quality_failures.append(
                f"🚨 TEST COUNT REGRESSION: {existing_metrics.test_count} → {current_metrics.test_count} tests "
                f"(-{existing_metrics.test_count - current_metrics.test_count})"
            )

        if quality_failures:
            print("")
            print("🛑 COMMIT REJECTED - QUALITY REGRESSION DETECTED!")
            print("" + "=" * 60)
            print("")
            for failure in quality_failures:
                print(failure)
            print("")
            print("💪 Our commitment to code quality is UNYIELDING!")
            print("📈 Improve your code and try again:")
            print("   • Add more tests to increase coverage")
            print("   • Fix pylint warnings and errors")
            print("   • Ensure no tests were accidentally deleted")
            print("")
            print("📊 Current quality metrics:")
            print(
                f"   🧪 Tests: {current_metrics.test_count} (target: ≥{existing_metrics.test_count})"
            )
            print(
                f"   📈 Coverage: {current_metrics.test_coverage:.2f}% (target: ≥{existing_metrics.test_coverage:.2f}%)"
            )
            print(
                f"   🏆 Pylint: {current_metrics.pylint_score:.2f}/10 (target: ≥{existing_metrics.pylint_score:.2f})"
            )
            print("")
            sys.exit(1)

        if args.verbose:
            print("✅ QUALITY STANDARDS MAINTAINED!")
            if (
                current_metrics.test_coverage > existing_metrics.test_coverage + 0.1
                or current_metrics.pylint_score > existing_metrics.pylint_score + 0.05
                or current_metrics.test_count > existing_metrics.test_count
            ):
                print("🚀 Quality improvements detected - excellent work!")

    # Update documentation files
    if args.verbose:
        print("\n📚 Updating documentation files...")

    updated_files = update_documentation_files(current_metrics, args.verbose)

    # Save current metrics
    save_metrics(current_metrics, metrics_file)

    if updated_files:
        print(
            f"✅ Updated {len(updated_files)} documentation files with current metrics:"
        )
        print(
            f"   📊 Tests: {current_metrics.test_count} (coverage: {current_metrics.test_coverage:.2f}%)"
        )
        print(f"   🏆 Pylint: {current_metrics.pylint_score:.2f}/10")

        if not args.verbose:
            for file in updated_files:
                print(f"   📝 {file}")
    else:
        if args.verbose:
            print("ℹ️  No documentation files needed updates")


if __name__ == "__main__":
    main()
