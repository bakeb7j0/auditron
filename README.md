# Auditron — Enterprise Host Auditing Suite

**Auditron** is a USB-hosted, agentless security and compliance auditing tool designed for CentOS 7.6 environments. It provides comprehensive system auditing capabilities through SSH-based remote execution, modular strategy architecture, and resumable audit sessions.

[![CI Status](https://github.com/analogic/auditron/workflows/CI/badge.svg)](https://github.com/analogic/auditron/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)](tests/)
[![Code Quality](https://img.shields.io/badge/pylint-9.17%2F10-brightgreen)](docs/test-plan.md)

## 🚀 Key Features

- **Agentless Architecture**: No software installation required on target systems
- **Modular Strategy System**: Plugin-based audit checks with easy extensibility
- **Resumable Sessions**: Continue interrupted audits without data loss
- **Comprehensive Coverage**: 6 implemented strategies, 8+ planned
- **Production Ready**: 111+ tests, enterprise-grade quality assurance
- **Security Focused**: Read-only posture with controlled privilege usage

## 📋 System Requirements

### Host System (USB Device)
- **Python**: 3.10+ (tested on 3.10, 3.11, 3.12)
- **Storage**: Minimum 64GB USB drive
- **OS**: Linux (development/testing), Windows WSL supported

### Target Systems
- **OS**: CentOS 7.6 (primary), future multi-OS support planned
- **Access**: SSH connectivity (port 22 or custom)
- **Authentication**: SSH keys (preferred) or password
- **Privileges**: Root access or sudo capabilities

## 🏗️ Project Structure

```
auditron/
├── auditron.py                 # Main orchestrator and CLI entry point
├── strategies/                 # Audit strategy implementations
│   ├── base.py                # Strategy interface and context
│   ├── rpm_inventory.py       # Package inventory collection
│   ├── rpm_verify.py          # File integrity verification
│   ├── processes.py           # Running process snapshots
│   ├── sockets.py             # Network service discovery
│   ├── osinfo.py              # System information collection
│   └── routes.py              # Network routing configuration
├── utils/                      # Core utilities
│   ├── ssh_runner.py          # SSH client and command execution
│   ├── db.py                  # Database operations and schema management
│   ├── parsing.py             # Command output parsers
│   └── compress.py            # Content compression and hashing
├── scripts/                    # Database and configuration utilities
│   ├── seed_db.py             # Database initialization and seeding
│   └── config_utility.py      # Interactive configuration management
├── tests/                      # Comprehensive test suite (111+ tests)
│   ├── test_*.py              # Unit tests for each component
│   ├── integration/           # End-to-end workflow tests
│   └── conftest.py            # Shared test fixtures and mocks
└── docs/                       # Comprehensive documentation
    ├── overview.md            # System overview and concepts
    ├── architecture.md        # Technical architecture details
    ├── check-specs.md         # Audit strategy specifications
    ├── security.md            # Security model and implementation
    ├── cli-bootstrap.md       # Command line usage guide
    └── seed-prompt.md         # Development context bootstrap
```

## ⚡ Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/analogic/auditron.git
cd auditron

# Create Python virtual environment
python3 -m venv auditron-env
source auditron-env/bin/activate  # Linux/Mac
# auditron-env\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Database Initialization

```bash
# Initialize database with schema and defaults
python scripts/seed_db.py auditron.db

# Configure target hosts interactively
python scripts/config_utility.py auditron.db
```

### 3. SSH Configuration

```bash
# Test SSH connectivity to target hosts
ssh -o BatchMode=yes root@target-host "echo 'Connection successful'"

# Set up SSH keys (recommended)
ssh-copy-id root@target-host

# Verify sudo access (if needed for future privilege separation)
ssh root@target-host "sudo -n whoami"
```

### 4. Execute Audit

```bash
# Start fresh audit session
python auditron.py --fresh

# Resume interrupted audit
python auditron.py --resume

# Use custom database location
python auditron.py --fresh --db /path/to/custom.db
```

## 🧪 Development and Testing

### Running Tests

```bash
# Run full test suite with coverage
pytest --cov=auditron --cov=utils --cov=strategies

# Run unit tests only (fast)
pytest -m "not integration"

# Run specific test categories
pytest -m db          # Database tests
pytest -m ssh         # SSH-related tests
pytest -m strategy    # Strategy implementation tests
```

### Code Quality

```bash
# Run all linting tools
ruff check .           # Primary linter
black --check .        # Code formatting
isort --check-only .   # Import sorting
flake8 .              # Style checking
pylint auditron.py utils/ strategies/  # Comprehensive analysis

# Auto-fix formatting issues
black .
isort .
```

### CI/CD Pipeline

The project includes comprehensive GitHub Actions CI/CD:
- **Multi-Python Testing**: 3.10, 3.11, 3.12
- **Complete Linting**: All tools passing
- **Coverage Reporting**: 75%+ threshold with current 92% coverage
- **Quality Gates**: Pylint score 9.17/10

## 📊 Current Implementation Status

### ✅ Implemented Strategies
- **RPM Inventory**: Complete package listing with metadata
- **RPM Verification**: File integrity checking with snapshots
- **Process Monitoring**: Running process inventory
- **Network Sockets**: Service discovery and port scanning
- **OS Information**: System identification and baseline
- **Routing State**: Network routing configuration capture

### 🚧 Planned Strategies
- User and Group Management
- Authentication and Login History
- Shell Command History Analysis
- System Service Inventory
- Firewall Configuration Capture
- Network Interface Configuration
- Hardware Inventory
- System Resource Monitoring

## 🔒 Security Model

### Read-Only Security Posture
- **No System Modifications**: Strict information-gathering only
- **Controlled Privileges**: Currently root access, future sudo separation
- **Command Auditing**: Complete execution logging
- **Data Protection**: Local storage only, content filtering

### Privacy Protection
- **Sensitive Data Filtering**: Automatic removal of passwords, keys
- **Content Size Limits**: Configurable snapshot size caps
- **Compression and Deduplication**: SHA-256 hashing, gzip compression
- **UTC Timestamps**: Consistent temporal correlation

## 📚 Documentation

### Core Documentation
- [**Architecture Overview**](docs/architecture.md) - System design and component interaction
- [**Check Specifications**](docs/check-specs.md) - Detailed audit strategy specifications
- [**Security Model**](docs/security.md) - Comprehensive security implementation
- [**CLI Usage Guide**](docs/cli-bootstrap.md) - Command line interface documentation
- [**Test Plan**](docs/test-plan.md) - Testing strategy and quality assurance

### Developer Resources
- [**Component Map**](docs/component-map.md) - Detailed component architecture
- [**Seed Prompt**](docs/seed-prompt.md) - Development context bootstrap
- [**Requirements**](docs/requirements-ears.md) - Authoritative business requirements

## 🛠️ Configuration Management

### Host Management
```bash
# Interactive configuration
python scripts/config_utility.py auditron.db

# Direct database manipulation
sqlite3 auditron.db "INSERT INTO hosts (hostname, ip, ssh_user, ssh_port) VALUES ('server1', '192.168.1.10', 'root', 22);"
```

### Strategy Control
```bash
# Disable strategy globally
sqlite3 auditron.db "UPDATE global_defaults SET nmap = 0 WHERE id = 1;"

# Host-specific overrides
sqlite3 auditron.db "INSERT INTO host_overrides (host_id, rpm_verify, max_snapshot_bytes) VALUES (1, 0, 1048576);"
```

## 🚀 Future Roadmap

### Short Term
- Multi-host parallel execution
- Enhanced progress reporting with rich/tqdm
- Additional audit strategies (users, services, firewall)

### Medium Term
- Multi-OS support with adaptive strategies
- On-site HTML/PDF report generation
- Performance optimization and resource management

### Long Term
- Real-time monitoring capabilities
- Advanced analytics and trend analysis
- Integration with external security tools

## 🤝 Contributing

### Development Workflow
1. **Test-Driven Development**: Write tests first for new features
2. **Quality Standards**: Maintain >90% test coverage for new code
3. **Code Review**: All changes require comprehensive review
4. **Documentation**: Update docs for all functional changes

### Code Standards
- **Linting**: All tools must pass (ruff, black, isort, flake8, pylint)
- **Testing**: Comprehensive unit and integration test coverage
- **Documentation**: Developer-focused technical documentation
- **Security**: Security-first design and implementation

## 📞 Support and Contact

- **Issues**: [GitHub Issues](https://github.com/analogic/auditron/issues)
- **Discussions**: [GitHub Discussions](https://github.com/analogic/auditron/discussions)
- **Documentation**: See `docs/` directory for comprehensive guides

## 📄 License

[Add license information here]

---

**Auditron** - Enterprise-grade host auditing for security professionals and system administrators.
