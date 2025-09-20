#!/usr/bin/env python3
"""Build deployment package for Auditron using PyInstaller.

This script creates a standalone executable package suitable for USB deployment.
The resulting binary includes all dependencies and can run on systems without
Python installed.

Usage:
    python scripts/build_deployment.py [--clean] [--test]
    
Options:
    --clean     Clean build directories before building
    --test      Run basic functionality tests after building
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    """Main build orchestration function."""
    parser = argparse.ArgumentParser(description="Build Auditron deployment package")
    parser.add_argument(
        "--clean", action="store_true", help="Clean build directories before building"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run basic tests after building"
    )
    parser.add_argument(
        "--output-dir",
        default="deployment",
        help="Output directory for deployment package (default: deployment)",
    )

    args = parser.parse_args()

    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent.resolve()
    os.chdir(project_root)

    print("🚀 Building Auditron deployment package...")
    print(f"📁 Project root: {project_root}")

    # Clean build directories if requested
    if args.clean:
        print("🧹 Cleaning build directories...")
        clean_build_dirs()

    # Verify PyInstaller is available
    if not check_pyinstaller():
        print("❌ PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)

    # Build the executable
    print("🔨 Building executable with PyInstaller...")
    if not build_executable():
        print("❌ Build failed!")
        sys.exit(1)

    # Create deployment package
    print("📦 Creating deployment package...")
    deployment_dir = create_deployment_package(args.output_dir)

    # Run tests if requested
    if args.test:
        print("🧪 Running post-build tests...")
        if not test_executable(deployment_dir):
            print("❌ Tests failed!")
            sys.exit(1)

    print("✅ Deployment package created successfully!")
    print(f"📍 Location: {deployment_dir}")
    print("💾 Ready for USB deployment")


def clean_build_dirs():
    """Remove PyInstaller build and dist directories."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"  Removing {dir_name}/")
            shutil.rmtree(dir_name)


def check_pyinstaller():
    """Verify PyInstaller is available."""
    try:
        result = subprocess.run(
            ["pyinstaller", "--version"], capture_output=True, text=True, check=True
        )
        print(f"  PyInstaller version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def build_executable():
    """Build the executable using PyInstaller."""
    try:
        # Run PyInstaller with our spec file
        subprocess.run(
            ["pyinstaller", "--clean", "auditron.spec"],
            check=True,
            capture_output=True,
            text=True,
        )

        # Check if executable was created
        executable_path = Path("dist/auditron")
        if not executable_path.exists():
            print(f"❌ Executable not found at {executable_path}")
            return False

        print(f"  ✅ Executable built: {executable_path}")
        print(f"  📏 Size: {executable_path.stat().st_size / 1024 / 1024:.1f} MB")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def create_deployment_package(output_dir):
    """Create complete deployment package with executable and supporting files."""
    deployment_dir = Path(output_dir).resolve()

    # Create deployment directory
    deployment_dir.mkdir(exist_ok=True)

    # Copy executable
    executable_src = Path("dist/auditron")
    executable_dst = deployment_dir / "auditron"
    shutil.copy2(executable_src, executable_dst)
    executable_dst.chmod(0o755)  # Ensure executable permissions

    # Copy database utilities
    scripts_dir = deployment_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Copy deployment-friendly scripts
    deployment_scripts = [
        "init_deployment_db.py",  # Deployment-friendly DB init
        "config_deployment.py",  # Deployment-friendly config utility
    ]

    for script in deployment_scripts:
        src = Path("scripts") / script
        if src.exists():
            shutil.copy2(src, scripts_dir / script)
            # Ensure executable permissions
            (scripts_dir / script).chmod(0o755)

    # Copy essential documentation
    docs_dir = deployment_dir / "docs"
    docs_dir.mkdir(exist_ok=True)

    essential_docs = [
        "schema.sql",
        "requirements-ears.md",
        "user-manual.md",
        "cli-bootstrap.md",
    ]

    for doc in essential_docs:
        src = Path("docs") / doc
        if src.exists():
            shutil.copy2(src, docs_dir / doc)

    # Create deployment README
    create_deployment_readme(deployment_dir)

    # Create sample configuration
    create_sample_config(deployment_dir)

    return deployment_dir


def create_deployment_readme(deployment_dir):
    """Create README for deployment package."""
    readme_content = """# Auditron USB Deployment Package

This package contains a standalone Auditron executable for USB deployment.

## Quick Start

1. **Initialize Database**:
   ```bash
   python3 scripts/init_deployment_db.py workspace/auditron.db --with-defaults
   ```

2. **Configure Hosts**:
   ```bash
   python3 scripts/config_deployment.py workspace/auditron.db
   ```

3. **Run Audit**:
   ```bash
   ./auditron --fresh --db auditron.db
   ```

## Files

- `auditron` - Main executable (no Python required on target system)
- `scripts/` - Database initialization and configuration utilities
- `docs/` - Essential documentation and schema files
- `sample-config.sql` - Sample host configuration

## Requirements

- Target systems: CentOS 7.6+ with SSH access
- USB drive: Minimum 1GB free space
- Network: SSH connectivity to target hosts

For complete documentation, see: docs/user-manual.md
"""

    readme_path = deployment_dir / "README.md"
    readme_path.write_text(readme_content)


def create_sample_config(deployment_dir):
    """Create sample configuration SQL file."""
    sample_config = """-- Sample Auditron host configuration
-- Customize these values for your environment

-- Add target hosts
INSERT INTO hosts (hostname, ip, ssh_user, ssh_port, ssh_key_path, use_sudo) VALUES
    ('server1.example.com', '192.168.1.10', 'root', 22, NULL, 0),
    ('server2.example.com', '192.168.1.11', 'audit', 22, '/path/to/key.pem', 1);

-- Configure global defaults (optional)
UPDATE global_defaults SET 
    max_snapshot_bytes = 1048576,  -- 1MB limit for file snapshots
    rpm_inventory = 1,
    rpm_verify = 1,
    processes = 1,
    sockets = 1,
    osinfo = 1,
    routes = 1
WHERE id = 1;

-- Host-specific overrides (optional)
-- INSERT INTO host_overrides (host_id, rpm_verify, max_snapshot_bytes) 
-- VALUES (1, 0, 512000);  -- Disable rpm_verify for host 1, smaller snapshots
"""

    config_path = deployment_dir / "sample-config.sql"
    config_path.write_text(sample_config)


def test_executable(deployment_dir):
    """Run basic functionality tests on the built executable."""
    executable = deployment_dir / "auditron"

    if not executable.exists():
        print("❌ Executable not found for testing")
        return False

    # Test help output
    try:
        result = subprocess.run(
            [str(executable), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        if "Auditron" in result.stdout and "Host auditing tool" in result.stdout:
            print("  ✅ Help output test passed")
        else:
            print("  ❌ Help output test failed - unexpected output")
            return False

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  ❌ Help test failed: {e}")
        return False

    print("  ✅ All basic tests passed")
    return True


if __name__ == "__main__":
    main()
