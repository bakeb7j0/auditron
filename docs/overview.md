# Auditron Overview

**Auditron** is a USB-hosted, agentless security and compliance auditing tool designed specifically for CentOS 7.6 environments. It provides comprehensive system auditing capabilities without requiring agent installation on target systems.

## Core Concept

Auditron operates as a portable auditing solution that:
- Runs from a USB drive with minimum 64GB storage
- Connects to target hosts via SSH (user/password or key-based)
- Executes modular audit checks using the Strategy pattern
- Stores all configuration and results in a local SQLite database
- Supports resumable audit sessions for large environments
- Provides granular control over which checks run on which hosts

## Target Environment

**Primary Target**: CentOS 7.6 (EOL, expect stale environments)
**Future**: OS detection and adaptation for other Linux distributions
**Deployment**: Single auditor system auditing multiple network hosts
**Scale**: Unlimited hosts (time-limited by serial execution)
**Access**: Currently designed to run as root via SSH (future: privilege separation)

## Key Features

### Agentless Architecture
- No software installation required on target systems
- SSH-based remote command execution
- Read-only security posture with controlled sudo usage
- Minimal network footprint

### Modular Strategy System
- Plugin-based audit checks in `strategies/` directory
- Easy addition of new audit capabilities
- Individual strategy enable/disable control
- Per-host configuration overrides

### Resumable Operations
- Session-based execution tracking
- Resume interrupted audits without data loss
- Progress indication during long-running audits
- Error recovery and continuation

### Comprehensive Data Collection
- System configuration snapshots
- Security state assessment
- Change detection and verification
- Structured data storage with deduplication

## Use Cases

### Security Auditing
- Compliance verification (internal standards)
- Change detection between audit periods
- Security configuration assessment
- Incident response data collection

### System Documentation
- Environment inventory and baseline establishment
- Configuration drift detection
- Asset management support
- Change tracking over time

## Operational Model

1. **Preparation**: Configure USB with Auditron, Python environment, and target host list
2. **Execution**: Connect to target network and run audit against configured hosts
3. **Collection**: All data stored locally in SQLite database on USB
4. **Analysis**: Return USB to engineering for result analysis and reporting
5. **Future**: On-site HTML/PDF report generation planned

## Development Context

**Target Users**: Analogic service and engineering personnel
**Development Team**: Software developers (this documentation audience)
**Quality Standards**: Enterprise-grade with comprehensive test suite (111+ tests)
**CI/CD**: Multi-Python version testing with full linting pipeline

For detailed technical specifications, see:
- `architecture.md` - System design and component interaction
- `check-specs.md` - Audit strategy specifications
- `data-model.md` - Database schema and relationships
- `requirements-ears.md` - Authoritative business requirements
