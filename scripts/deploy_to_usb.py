#!/usr/bin/env python3
"""Deploy Auditron to USB drive for field deployment.

This script copies the built Auditron deployment package to a USB drive,
sets up the directory structure, and creates convenience scripts for
easy operation in the field.

Usage:
    python scripts/deploy_to_usb.py /path/to/usb/mount [--deployment-dir deployment]
    
Example:
    python scripts/deploy_to_usb.py /media/user/AUDITRON_USB
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def main():
    """Main USB deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Auditron package to USB drive")
    parser.add_argument(
        "usb_path", help="Path to mounted USB drive (e.g., /media/user/AUDITRON_USB)"
    )
    parser.add_argument(
        "--deployment-dir",
        default="deployment",
        help="Source deployment directory (default: deployment)",
    )
    parser.add_argument(
        "--usb-dir",
        default="auditron",
        help="Directory name on USB drive (default: auditron)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing deployment on USB"
    )

    args = parser.parse_args()

    usb_path = Path(args.usb_path).resolve()
    deployment_dir = Path(args.deployment_dir).resolve()
    usb_auditron_dir = usb_path / args.usb_dir

    print("💾 Deploying Auditron to USB drive...")
    print(f"📁 Source: {deployment_dir}")
    print(f"🔌 USB path: {usb_path}")
    print(f"📂 Target: {usb_auditron_dir}")

    # Validate inputs
    if not validate_deployment(deployment_dir, usb_path, usb_auditron_dir, args.force):
        sys.exit(1)

    # Deploy to USB
    if not deploy_to_usb(deployment_dir, usb_auditron_dir):
        sys.exit(1)

    # Create convenience scripts
    create_usb_scripts(usb_auditron_dir)

    # Create workspace directories
    create_workspace_dirs(usb_auditron_dir)

    print("✅ USB deployment completed successfully!")
    print("🎯 Ready for field deployment")
    print("📋 Next steps:")
    print("   1. Safely eject USB drive")
    print(f"   2. On target system, run: cd {args.usb_dir} && ./setup.sh")
    print(
        "   3. Configure hosts: python3 scripts/config_deployment.py workspace/auditron.db"
    )
    print("   4. Execute audit: ./run_audit.sh")


def validate_deployment(deployment_dir, usb_path, usb_auditron_dir, force):
    """Validate deployment prerequisites."""

    # Check deployment directory exists
    if not deployment_dir.exists():
        print(f"❌ Deployment directory not found: {deployment_dir}")
        print("   Run: python scripts/build_deployment.py first")
        return False

    # Check auditron executable exists
    executable = deployment_dir / "auditron"
    if not executable.exists():
        print(f"❌ Auditron executable not found: {executable}")
        return False

    # Check USB path is accessible
    if not usb_path.exists():
        print(f"❌ USB path not accessible: {usb_path}")
        return False

    # Check if target already exists
    if usb_auditron_dir.exists():
        if not force:
            print(f"❌ Target directory already exists: {usb_auditron_dir}")
            print("   Use --force to overwrite")
            return False
        else:
            print(f"⚠️  Overwriting existing deployment: {usb_auditron_dir}")

    # Check USB has enough space (estimate 100MB needed)
    try:
        statvfs = os.statvfs(usb_path)
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        needed_bytes = 100 * 1024 * 1024  # 100MB

        if free_bytes < needed_bytes:
            print(
                f"❌ Insufficient USB space. Need ~100MB, have {free_bytes // 1024 // 1024}MB"
            )
            return False

        print(f"💾 USB free space: {free_bytes // 1024 // 1024}MB")

    except OSError as e:
        print(f"⚠️  Could not check USB space: {e}")

    return True


def deploy_to_usb(deployment_dir, usb_auditron_dir):
    """Copy deployment package to USB drive."""
    try:
        # Remove existing if present
        if usb_auditron_dir.exists():
            shutil.rmtree(usb_auditron_dir)

        # Copy entire deployment directory
        print("📋 Copying deployment files...")
        shutil.copytree(deployment_dir, usb_auditron_dir)

        # Ensure executable permissions are preserved
        executable = usb_auditron_dir / "auditron"
        if executable.exists():
            executable.chmod(0o755)
            print(f"  ✅ Executable: {executable}")

        # Set permissions on Python scripts
        for script_file in (usb_auditron_dir / "scripts").glob("*.py"):
            script_file.chmod(0o755)

        return True

    except (OSError, shutil.Error) as e:
        print(f"❌ Failed to copy deployment: {e}")
        return False


def create_usb_scripts(usb_auditron_dir):
    """Create convenience scripts for USB deployment."""

    # Setup script
    setup_script = usb_auditron_dir / "setup.sh"
    setup_content = """#!/bin/bash
# Auditron USB Setup Script
set -e

echo "🚀 Setting up Auditron workspace..."

# Create workspace directory
mkdir -p workspace

# Initialize database if it doesn't exist
if [ ! -f workspace/auditron.db ]; then
    echo "📊 Initializing database..."
    python3 scripts/init_deployment_db.py workspace/auditron.db --with-defaults
    echo "✅ Database initialized"
else
    echo "📊 Database already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure hosts: python3 scripts/config_deployment.py workspace/auditron.db"
echo "2. Run audit: ./run_audit.sh"
echo ""
"""
    setup_script.write_text(setup_content)
    setup_script.chmod(0o755)

    # Run audit script
    run_audit_script = usb_auditron_dir / "run_audit.sh"
    run_audit_content = """#!/bin/bash
# Auditron Execution Script
set -e

DB_PATH="workspace/auditron.db"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found. Run ./setup.sh first"
    exit 1
fi

# Check if hosts are configured
HOST_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM hosts;" 2>/dev/null || echo "0")
if [ "$HOST_COUNT" -eq 0 ]; then
    echo "❌ No hosts configured. Run:"
    echo "   python3 scripts/config_deployment.py $DB_PATH"
    exit 1
fi

echo "🚀 Starting Auditron audit session..."
echo "📊 Database: $DB_PATH"
echo "🖥️  Target hosts: $HOST_COUNT"
echo ""

# Execute audit
./auditron --fresh --db "$DB_PATH"

echo ""
echo "✅ Audit completed!"
echo "📊 Results stored in: $DB_PATH"
"""
    run_audit_script.write_text(run_audit_content)
    run_audit_script.chmod(0o755)

    # Resume audit script
    resume_script = usb_auditron_dir / "resume_audit.sh"
    resume_content = """#!/bin/bash
# Auditron Resume Script
set -e

DB_PATH="workspace/auditron.db"

echo "🔄 Resuming Auditron audit session..."
./auditron --resume --db "$DB_PATH"
echo "✅ Resume completed!"
"""
    resume_script.write_text(resume_content)
    resume_script.chmod(0o755)

    print("  ✅ Created setup.sh")
    print("  ✅ Created run_audit.sh")
    print("  ✅ Created resume_audit.sh")


def create_workspace_dirs(usb_auditron_dir):
    """Create workspace directories for runtime data."""
    workspace_dir = usb_auditron_dir / "workspace"
    workspace_dir.mkdir(exist_ok=True)

    # Create logs directory
    logs_dir = workspace_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create exports directory for future reporting
    exports_dir = workspace_dir / "exports"
    exports_dir.mkdir(exist_ok=True)

    # Create .gitkeep files so directories are preserved
    (logs_dir / ".gitkeep").touch()
    (exports_dir / ".gitkeep").touch()

    print("  ✅ Created workspace directories")


if __name__ == "__main__":
    main()
