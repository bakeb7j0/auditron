# Auditron Deployment Guide

This guide covers building and deploying Auditron as a standalone executable for USB-based field deployments.

## Overview

Auditron uses **PyInstaller** to create a single executable that includes all dependencies, eliminating the need for Python installations on target systems. This approach is ideal for:

- **USB Deployment**: Portable auditing tool on removable media
- **Air-Gapped Environments**: No internet connectivity required
- **Consistent Runtime**: Same Python version/dependencies everywhere
- **Enterprise Security**: No software installation on target systems

## Prerequisites

### Development System

- **Python**: 3.10+ (3.11+ recommended)
- **PyInstaller**: 6.0+ (installed automatically)
- **Storage**: ~200MB for build artifacts
- **OS**: Linux (primary), Windows/macOS (experimental)

### Target Systems

- **CentOS**: 7.6+ (primary target)
- **SSH Access**: Port 22 or custom
- **Authentication**: SSH keys (preferred) or password
- **Storage**: 64GB+ USB drive for deployment

## Quick Start

### 1. Build Deployment Package

```bash
# Install dependencies and build
make build-test

# Or with manual steps:
pip install pyinstaller
python scripts/build_deployment.py --clean --test
```

### 2. Deploy to USB

```bash
# Set USB mount point and deploy
USB_PATH=/media/user/AUDITRON make deploy-usb

# Or manually:
python scripts/deploy_to_usb.py /path/to/usb/mount
```

### 3. Field Deployment

On target system with USB drive:

```bash
cd /path/to/usb/auditron
./setup.sh
python3 scripts/config_utility.py workspace/auditron.db
./run_audit.sh
```

## Build Process Details

### Build Scripts

#### `scripts/build_deployment.py`

Creates standalone deployment package with PyInstaller:

```bash
python scripts/build_deployment.py [options]

Options:
  --clean         Clean build directories first
  --test          Run post-build functionality tests  
  --output-dir    Custom output directory (default: deployment)
```

**Output Structure:**
```
deployment/
├── auditron                    # Main executable (no Python required)
├── scripts/                    # Database utilities (require Python)
│   ├── seed_db.py             # Database initialization
│   └── config_utility.py      # Host configuration
├── docs/                       # Essential documentation
│   ├── schema.sql             # Database schema
│   ├── user-manual.md         # User documentation
│   └── ...
├── sample-config.sql           # Example configuration
└── README.md                   # Deployment instructions
```

#### `scripts/deploy_to_usb.py`

Copies deployment package to USB with field-ready scripts:

```bash
python scripts/deploy_to_usb.py USB_PATH [options]

Options:
  --deployment-dir DIR    Source deployment directory
  --usb-dir DIR          Target directory on USB
  --force                Overwrite existing deployment
```

**USB Structure:**
```
/path/to/usb/auditron/
├── auditron                    # Main executable
├── scripts/                    # Database utilities  
├── docs/                       # Documentation
├── workspace/                  # Runtime workspace
│   ├── logs/                  # Execution logs
│   └── exports/               # Report exports (future)
├── setup.sh                   # Field setup script
├── run_audit.sh              # Execute audit
├── resume_audit.sh           # Resume interrupted audit
├── sample-config.sql         # Configuration template
└── README.md                 # Field instructions
```

### PyInstaller Configuration

The `auditron.spec` file defines the build configuration:

**Key Features:**
- **Single File**: All dependencies bundled into one executable
- **Hidden Imports**: Explicit inclusion of strategy modules
- **Data Files**: Database schema and docs included
- **Exclusions**: Development/test dependencies removed
- **Compression**: UPX compression enabled (if available)
- **Console Mode**: Maintains CLI interface

**Size Optimization:**
- Excludes test frameworks (pytest, etc.)
- Removes linting tools (ruff, black, etc.)
- Strips unnecessary standard library modules
- Enables UPX compression for smaller binaries

## Field Deployment Workflow

### 1. USB Preparation

```bash
# Format USB drive (optional)
sudo mkfs.ext4 /dev/sdX1 -L "AUDITRON"

# Mount USB
mkdir -p /media/user/AUDITRON
sudo mount /dev/sdX1 /media/user/AUDITRON

# Deploy Auditron
USB_PATH=/media/user/AUDITRON make deploy-usb
```

### 2. Target System Setup

```bash
# Navigate to USB Auditron directory
cd /media/user/AUDITRON/auditron

# Run setup (creates workspace, initializes database)
./setup.sh

# Configure target hosts
python3 scripts/config_utility.py workspace/auditron.db
```

**Host Configuration Options:**

```sql
-- Example host configuration
INSERT INTO hosts (hostname, ip, ssh_user, ssh_port, ssh_key_path, use_sudo) VALUES
    ('server1', '192.168.1.10', 'root', 22, NULL, 0),
    ('server2', '192.168.1.11', 'audit', 22, '/path/to/key.pem', 1);
```

### 3. Audit Execution

```bash
# Start fresh audit
./run_audit.sh

# Resume interrupted audit  
./resume_audit.sh

# Manual execution with options
./auditron --fresh --db workspace/auditron.db
./auditron --resume --db workspace/auditron.db
```

## Makefile Integration

The deployment process is integrated into the project Makefile:

```bash
# Development
make install           # Install dev dependencies
make test             # Run tests
make lint             # Code quality checks
make format           # Auto-format code

# Deployment
make install-deploy   # Install PyInstaller
make build           # Build deployment package  
make build-test      # Build with functionality tests
make package         # Show package contents
make deploy-usb      # Deploy to USB (set USB_PATH)

# Cleanup
make clean           # Clean build artifacts
make clean-all       # Clean everything including venv
```

## Troubleshooting

### Build Issues

**PyInstaller Not Found:**
```bash
pip install pyinstaller
# or
make install-deploy
```

**Import Errors in Executable:**
- Check `auditron.spec` hiddenimports
- Add missing modules to hiddenimports list
- Verify module paths are correct

**Large Executable Size:**
- Review excludes in `auditron.spec`
- Install UPX compressor: `sudo apt install upx-ucl`
- Consider splitting data files if needed

### Runtime Issues

**Database Errors:**
```bash
# Reinitialize database
rm workspace/auditron.db
python3 scripts/seed_db.py workspace/auditron.db
```

**SSH Connection Failures:**
- Verify network connectivity: `ping target-host`
- Test SSH manually: `ssh user@target-host`
- Check SSH key permissions: `chmod 600 /path/to/key`
- Verify SSH configuration in database

**Permission Errors:**
```bash
# Fix executable permissions
chmod +x auditron *.sh

# Fix script permissions  
chmod +x scripts/*.py
```

### USB Issues

**Mount Problems:**
```bash
# List available devices
lsblk

# Manual mount
sudo mount /dev/sdX1 /mnt/usb

# Check filesystem
sudo fsck /dev/sdX1
```

**Space Issues:**
- Use 64GB+ USB drives
- Clean old deployments before new ones
- Monitor space: `df -h /path/to/usb`

## Advanced Configuration

### Custom Build Options

**Modify PyInstaller Spec:**
Edit `auditron.spec` for custom build requirements:

```python
# Add custom data files
datas=[
    ('custom_data/*', 'custom_data'),
    # ...
],

# Additional hidden imports
hiddenimports=[
    'custom_module',
    # ...
],
```

**Build Script Customization:**
Modify `scripts/build_deployment.py` for:
- Custom output directories
- Additional validation steps
- Platform-specific handling

### Multi-Platform Builds

**Linux (Primary):**
```bash
# Native build
make build-test
```

**Windows (Cross-Platform):**
```bash
# Requires Windows system or Wine
pip install pyinstaller[encryption]
python scripts/build_deployment.py --clean
```

**Docker Builds:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install pyinstaller
RUN python scripts/build_deployment.py --clean
```

### Security Considerations

**USB Security:**
- Encrypt USB drives for sensitive environments
- Use read-only mode during audits when possible
- Verify USB integrity before deployment

**Network Security:**
- Use SSH key authentication
- Limit SSH access to audit accounts only
- Monitor SSH connections during audits
- Use bastion hosts in secure environments

**Data Protection:**
- Regular database backups
- Secure transport of audit results
- Data retention policy compliance
- Sanitize sensitive data in logs

## Integration with CI/CD

**GitHub Actions:**
```yaml
- name: Build Deployment Package
  run: |
    make install-deploy
    make build-test

- name: Upload Deployment Artifacts  
  uses: actions/upload-artifact@v3
  with:
    name: auditron-deployment
    path: deployment/
```

**GitLab CI:**
```yaml
build_deployment:
  script:
    - make install-deploy
    - make build-test
  artifacts:
    paths:
      - deployment/
    expire_in: 1 week
```

## Performance Optimization

**Build Performance:**
- Use SSD storage for build process
- Parallel builds: `export MAKEFLAGS="-j$(nproc)"`
- Cache PyInstaller builds between iterations

**Runtime Performance:**
- Pre-warm SSH connections
- Optimize database queries
- Use connection pooling for multiple hosts
- Monitor resource usage during audits

**Storage Optimization:**
- Compress audit results
- Rotate logs automatically  
- Clean temporary files
- Use incremental backups

## Support and Maintenance

**Version Management:**
- Tag releases: `git tag v1.0.0`
- Include version in executable: Update `auditron.spec`
- Maintain deployment compatibility

**Updates:**
- Test new builds thoroughly
- Maintain backward compatibility
- Document breaking changes
- Provide migration scripts

**Monitoring:**
- Log deployment events
- Monitor USB health
- Track audit success rates
- Performance metrics collection

For additional support, see:
- [User Manual](user-manual.md) - Field operations
- [Architecture](architecture.md) - System design  
- [Security](security.md) - Security implementation