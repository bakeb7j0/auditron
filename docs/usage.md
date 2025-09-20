# Auditron Command-Line Usage Guide

This document provides comprehensive usage information for all Auditron command-line utilities, including required and optional parameters, examples, and return codes.

## Main Executable

### `auditron` (Main Auditing Tool)

**Description:** The primary Auditron executable that performs host auditing by executing modular strategies via SSH. Can start fresh audit sessions or resume interrupted ones.

**Usage:**
```bash
auditron [--db DATABASE] {--fresh | --resume | MODE}
```

**Arguments:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `MODE` | Positional | No* | None | Run mode: `fresh` or `resume` |
| `--db DATABASE` | Optional | No | `auditron.db` | Path to SQLite database file |
| `--fresh` | Flag | No* | False | Start a fresh audit session |
| `--resume` | Flag | No* | False | Resume the last unfinished session |

*Either `MODE` or `--fresh`/`--resume` must be specified.

**Examples:**
```bash
# Start fresh audit with default database
auditron --fresh

# Resume interrupted audit
auditron --resume

# Use custom database location  
auditron --fresh --db /path/to/audit.db

# Positional mode syntax (legacy)
auditron fresh
auditron resume
```

**Return Codes:**
- `0`: Audit completed successfully
- `1`: Configuration error (missing hosts, invalid arguments)
- `2`: Database error (schema issues, connection problems) 
- `3`: SSH connection failures to all hosts
- `4`: Partial failures (some hosts unreachable)

**Prerequisites:**
- Database must exist and contain configured hosts
- SSH connectivity to target hosts
- Valid authentication (SSH keys or passwords)

---

## Database Management

### `scripts/seed_db.py` (Legacy Database Seeder)

**Description:** Legacy database initialization script that creates schema and adds hosts/defaults. Uses hardcoded database path `db/auditron.db`.

**Usage:**
```bash
python scripts/seed_db.py [--init-defaults] [--add-host NAME --ip IP] [OPTIONS]
```

**Arguments:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--init-defaults` | Flag | No | False | Initialize global default settings |
| `--add-host NAME` | Option | No | None | Hostname to add (requires --ip) |
| `--ip IP` | Option | Conditional | None | IP address (required with --add-host) |
| `--user USER` | Option | No | `root` | SSH username |
| `--key KEY` | Option | No | None | SSH private key path |
| `--port PORT` | Option | No | `22` | SSH port number |
| `--sudo` | Flag | No | False | Enable sudo usage for this host |

**Examples:**
```bash
# Initialize database with defaults
python scripts/seed_db.py --init-defaults

# Add a host with SSH key
python scripts/seed_db.py --add-host web01 --ip 192.168.1.10 --key /path/to/key.pem

# Add host with custom user and sudo
python scripts/seed_db.py --add-host db01 --ip 192.168.1.20 --user audit --sudo
```

**Return Codes:**
- `0`: Operation completed successfully
- `1`: Missing required parameters or database error
- `2`: SQL constraint violation or schema error

**Limitations:**
- Fixed database path: `db/auditron.db`
- Creates parent directories automatically
- Overwrites existing schema on each run

---

### `scripts/config_utility.py` (Interactive Configuration)

**Description:** Interactive terminal-based utility for managing hosts, global defaults, and per-host overrides. Uses hardcoded database path `db/auditron.db`.

**Usage:**
```bash
python scripts/config_utility.py
```

**Arguments:**
- No command-line arguments (fully interactive)

**Interactive Menu Options:**

| Option | Description | Sub-operations |
|--------|-------------|----------------|
| `1` | List hosts | Display all configured hosts with details |
| `2` | Add host | Interactively configure hostname, IP, SSH settings |
| `3` | Remove host | Delete host by ID |
| `4` | Global default checks & limits | Enable/disable strategies, set limits |
| `5` | Per-host overrides | Override global settings for specific hosts |
| `q` | Quit | Exit the utility |

**Global Defaults Menu:**
- Toggle audit strategies (rpm_inventory, rpm_verify, processes, sockets, osinfo, routes)
- Set `max_snapshot_bytes` limit
- Configure `gzip_snapshots` compression
- Set `command_timeout_sec` values

**Host Overrides Menu:**
- Override any global setting for specific hosts
- Set to NULL to inherit global defaults
- Configure host-specific limits and timeouts

**Examples:**
```bash
# Start interactive configuration
python scripts/config_utility.py

# Example session:
# > 2 (Add host)
# Hostname: web-server-01
# IP: 192.168.1.100
# SSH user [root]: admin
# SSH key path (optional): /home/user/.ssh/audit_key
# SSH port [22]: 2222
# Use sudo? [y/N]: y
```

**Return Codes:**
- `0`: Normal exit
- `1`: Database connection error
- `2`: Database schema error or corruption

---

## Deployment Tools

### `scripts/build_deployment.py` (PyInstaller Builder)

**Description:** Creates standalone executable deployment package using PyInstaller. Bundles all dependencies into a single binary suitable for USB deployment.

**Usage:**
```bash
python scripts/build_deployment.py [OPTIONS]
```

**Arguments:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--clean` | Flag | No | False | Clean build directories before building |
| `--test` | Flag | No | False | Run functionality tests after building |
| `--output-dir DIR` | Option | No | `deployment` | Output directory for deployment package |

**Examples:**
```bash
# Basic build
python scripts/build_deployment.py

# Clean build with tests
python scripts/build_deployment.py --clean --test

# Custom output directory
python scripts/build_deployment.py --output-dir /tmp/auditron-build
```

**Output Structure:**
```
deployment/
├── auditron              # Standalone executable (~6MB)
├── scripts/              # Database utilities (require Python)
├── docs/                 # Essential documentation  
├── sample-config.sql     # Configuration examples
└── README.md            # Deployment instructions
```

**Return Codes:**
- `0`: Build completed successfully
- `1`: PyInstaller not found or not installed
- `2`: Build failed (compilation errors)
- `3`: Post-build tests failed (if --test used)

**Prerequisites:**
- PyInstaller 6.0+ installed (`pip install pyinstaller`)
- All project dependencies available
- ~200MB free disk space for build artifacts

---

### `scripts/deploy_to_usb.py` (USB Deployment)

**Description:** Copies deployment package to USB drive and creates field-ready scripts for easy operation.

**Usage:**
```bash
python scripts/deploy_to_usb.py USB_PATH [OPTIONS]
```

**Arguments:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `USB_PATH` | Positional | Yes | None | Path to mounted USB drive |
| `--deployment-dir DIR` | Option | No | `deployment` | Source deployment directory |
| `--usb-dir DIR` | Option | No | `auditron` | Target directory name on USB |
| `--force` | Flag | No | False | Overwrite existing deployment |

**Examples:**
```bash
# Deploy to USB drive
python scripts/deploy_to_usb.py /media/user/AUDITRON

# Force overwrite existing deployment
python scripts/deploy_to_usb.py /media/user/AUDITRON --force

# Custom source and target directories
python scripts/deploy_to_usb.py /mnt/usb --deployment-dir custom-build --usb-dir audit-tools
```

**USB Structure Created:**
```
/usb/auditron/
├── auditron             # Main executable
├── scripts/             # Database utilities
├── docs/                # Documentation
├── workspace/           # Runtime workspace
├── setup.sh            # Field setup script  
├── run_audit.sh        # Execute audit script
├── resume_audit.sh     # Resume audit script
└── sample-config.sql   # Configuration template
```

**Return Codes:**
- `0`: USB deployment completed successfully
- `1`: USB path not accessible or deployment directory missing
- `2`: Insufficient USB space (~100MB required)
- `3`: File copy operation failed
- `4`: Permission errors setting executable bits

---

### `scripts/test_config_input.py` (Automated Configuration)

**Description:** Provides automated test input to config_deployment.py for testing and demonstration purposes. Creates sample hosts and configuration.

**Usage:**
```bash
python scripts/test_config_input.py DATABASE_PATH
```

**Arguments:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `DATABASE_PATH` | Positional | Yes | None | Path to existing SQLite database file |

**Test Data Created:**
- **web-server-01**: 192.168.1.100, root user, SSH key auth, port 22, sudo enabled
- **db-server-01**: 192.168.1.200, dbadmin user, SSH key auth, port 2222, sudo disabled

**Examples:**
```bash
# Initialize database first
python scripts/init_deployment_db.py test.db --with-defaults

# Add test configuration
python scripts/test_config_input.py test.db

# Verify results
sqlite3 test.db "SELECT hostname, ip, ssh_user FROM hosts;"
```

**Return Codes:**
- `0`: Configuration completed successfully
- `1`: Database not found or configuration failed
- `2`: Script timeout or interruption

**Use Cases:**
- Automated testing of deployment packages
- Demonstration of configuration process
- Template for batch host configuration
- CI/CD pipeline integration

---

### `scripts/test_deployment.py` (Deployment Validation)

**Description:** Validates deployment package integrity and tests basic functionality without requiring target hosts.

**Usage:**
```bash
python scripts/test_deployment.py [OPTIONS]
```

**Arguments:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--deployment-dir DIR` | Option | No | `deployment` | Deployment directory to test |

**Test Categories:**
1. **Structure Validation:** Verifies all required files present
2. **Executable Functionality:** Tests help output and error handling
3. **Database Operations:** Tests schema creation and utilities

**Examples:**
```bash
# Test default deployment package
python scripts/test_deployment.py

# Test custom deployment directory
python scripts/test_deployment.py --deployment-dir /tmp/custom-build
```

**Return Codes:**
- `0`: All tests passed, deployment ready for field use
- `1`: Critical files missing or executable non-functional
- `2`: Database initialization problems
- `3`: Permission or access errors

---

## Development and Testing

### `minimal_test_runner.py` (Basic Validation)

**Description:** Lightweight test runner that validates project setup and basic functionality without requiring full pytest installation.

**Usage:**
```bash
python minimal_test_runner.py
```

**Arguments:**
- No command-line arguments

**Test Categories:**
1. Basic Python functionality and imports
2. Project-specific module imports
3. Database operations (create, schema, queries)
4. Parsing functions (RPM, SS output)
5. SSH runner classes
6. Strategy base classes
7. Test file structure validation
8. Pytest syntax checking

**Examples:**
```bash
# Run all validation tests
python minimal_test_runner.py
```

**Return Codes:**
- `0`: All validation tests passed, project ready for development
- `1`: Some validation tests failed, issues need resolution

**Output Sample:**
```
🔍 Minimal Auditron Test Validation
==================================================
--- Basic Functionality ---
✓ Basic imports successful
--- Project Imports ---  
✓ Utils imports successful
✓ Strategies imports successful
...
Results: 8/8 tests passed
🎉 All validation tests passed!
```

---

### `validate_tests.py` (Test Structure Checker)

**Description:** Validates test suite structure and ensures all required test files and fixtures are present.

**Usage:**
```bash
python validate_tests.py
```

**Arguments:**
- No command-line arguments

**Validation Checks:**
1. Required test files exist (`test_*.py`)
2. Conftest.py contains required fixtures
3. Pytest.ini has proper configuration
4. Integration test directory structure

**Examples:**
```bash
# Validate test structure
python validate_tests.py
```

**Return Codes:**
- `0`: Test structure is valid and complete
- `1`: Missing files, fixtures, or configuration errors

---

### `run_validation.py` (Comprehensive Validation)

**Description:** Comprehensive validation script that checks structure, imports, and pytest execution capabilities.

**Usage:**
```bash
python run_validation.py
```

**Arguments:**
- No command-line arguments

**Validation Steps:**
1. Test file structure validation
2. Import testing for all modules
3. Pytest execution test with sample test
4. Configuration verification

**Examples:**
```bash
# Run comprehensive validation
python run_validation.py
```

**Return Codes:**
- `0`: All validation passed, ready for full test execution
- `1`: Validation failed, issues must be resolved

---

## Field Operation Scripts

### USB Field Scripts (Created by deploy_to_usb.py)

#### `setup.sh` (Field Setup)

**Description:** Initializes workspace and database on target system.

**Usage:**
```bash
./setup.sh
```

**Operations:**
- Creates `workspace/` directory structure
- Initializes `workspace/auditron.db` if missing
- Sets up logging and export directories

**Return Codes:**
- `0`: Setup completed successfully
- `1`: Database initialization failed
- `2`: Permission or filesystem errors

#### `run_audit.sh` (Execute Audit)

**Description:** Executes fresh audit session with validation checks.

**Usage:**
```bash
./run_audit.sh
```

**Validation:**
- Checks database exists
- Verifies hosts are configured
- Confirms SSH connectivity

**Return Codes:**
- `0`: Audit completed successfully
- `1`: Configuration errors (no database, no hosts)
- `2`: SSH connectivity failures
- `3`: Audit execution errors

#### `resume_audit.sh` (Resume Audit)

**Description:** Resumes interrupted audit session.

**Usage:**
```bash
./resume_audit.sh
```

**Return Codes:**
- `0`: Resume completed successfully
- `1`: No session to resume
- `2`: Resume operation failed

---

## Integration with Make

All deployment tools are integrated with the project Makefile:

```bash
# Install deployment dependencies
make install-deploy

# Build deployment package
make build              # Basic build
make build-test         # Build with tests

# Deploy to USB (set USB_PATH environment variable)
USB_PATH=/media/user/AUDITRON make deploy-usb

# Validation and testing
make test               # Quick tests
make test-all          # Full test suite with coverage
make check             # Lint + test

# Cleanup
make clean             # Clean build artifacts
make clean-all         # Clean everything including venv
```

---

## Error Handling and Troubleshooting

### Common Return Codes

| Code | Category | Description | Resolution |
|------|----------|-------------|------------|
| `0` | Success | Operation completed successfully | None required |
| `1` | Config Error | Missing configuration, invalid parameters | Check arguments, verify config |
| `2` | Database Error | Schema issues, connection problems | Verify database, check permissions |
| `3` | Network Error | SSH failures, connectivity issues | Test SSH manually, check network |
| `4` | Partial Failure | Some operations succeeded, others failed | Review logs, retry failed operations |

### Diagnostic Commands

```bash
# Test SSH connectivity
ssh -o BatchMode=yes user@target-host "echo 'Connection OK'"

# Verify database schema
sqlite3 auditron.db ".schema" | head -20

# Check executable permissions
ls -la auditron scripts/*.py

# Validate deployment structure  
python scripts/test_deployment.py

# Run basic validation
python minimal_test_runner.py
```

---

## Security Considerations

### Database Security
- Database files contain sensitive host information
- Use appropriate file permissions (600/640)
- Consider encryption for sensitive environments

### SSH Security  
- Prefer SSH key authentication over passwords
- Use dedicated audit accounts with limited privileges
- Monitor SSH access during audits
- Use bastion hosts in secure environments

### USB Security
- Encrypt USB drives for sensitive deployments
- Use read-only mode during audits when possible
- Verify USB integrity before field deployment
- Implement secure transport for audit results

---

For additional information, see:
- [Architecture Guide](architecture.md) - System design details
- [Deployment Guide](deployment.md) - Complete deployment process
- [User Manual](user-manual.md) - Field operations guide
- [Security Model](security.md) - Security implementation details