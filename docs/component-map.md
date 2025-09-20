# Auditron Component Architecture Map

## Core System Components

### Orchestration Layer

| Component | File | Purpose | Key Functions | Dependencies |
|-----------|------|---------|---------------|-------------|
| **Main Orchestrator** | `auditron.py` | Entry point, CLI parsing, session management, host iteration | `parse_cli()`, `run_mode()`, `run_resume()`, `run_all_checks()` | `utils/db.py`, `utils/ssh_runner.py`, `strategies/*` |
| **CLI Interface** | `auditron.py` | Command line argument parsing with backward compatibility | Handles `--fresh/--resume` flags, database path, mode validation | `argparse` standard library |

### Data Layer

| Component | File | Purpose | Key Functions | Dependencies |
|-----------|------|---------|---------------|-------------|
| **Database Manager** | `utils/db.py` | SQLite operations, schema management, session tracking | `connect()`, `ensure_schema()`, `new_session()`, `start_check()` | `docs/schema.sql`, `sqlite3` |
| **Schema Definition** | `docs/schema.sql` | Database structure, constraints, relationships | Table definitions, indexes, foreign keys, check constraints | SQLite SQL syntax |
| **Data Compression** | `utils/compress.py` | Content compression and hashing for deduplication | `gz_bytes()`, `sha256_bytes()`, file snapshot optimization | `hashlib`, `gzip`, `base64` |

### Network Layer

| Component | File | Purpose | Key Functions | Dependencies |
|-----------|------|---------|---------------|-------------|
| **SSH Manager** | `utils/ssh_runner.py` | SSH connection management, command execution, tool detection | `SSHClient.run()`, `which()` caching, timeout/error handling | `subprocess`, `shlex` |
| **Command Parsing** | `utils/parsing.py` | Parse structured command outputs into database records | `parse_rpm_verify()`, `parse_socket_output()`, format-specific parsers | None (pure parsing logic) |

## Strategy Implementation Layer

### Base Strategy Framework

| Component | File | Purpose | Key Classes/Functions | Status |
|-----------|------|---------|----------------------|--------|
| **Strategy Interface** | `strategies/base.py` | Abstract base class and context definition | `AuditCheck`, `AuditContext`, `probe()`, `run()` | ✅ Complete |
| **Strategy Registry** | `strategies/__init__.py` | Strategy discovery and registration | Import all strategies, build `REGISTRY` dict | 📝 Planned |

### Implemented Audit Strategies

| Strategy | File | Purpose | Commands Used | Database Tables | Requirements |
|----------|------|---------|---------------|-----------------|-------------|
| **RPM Inventory** | `strategies/rpm_inventory.py` | Installed package listing | `rpm -qa --qf ...` | `rpm_packages` | `rpm` |
| **RPM Verification** | `strategies/rpm_verify.py` | File integrity checking | `rpm -Va`, `stat`, `cat` | `rpm_verified_files`, `file_meta`, `file_snapshots` | `rpm` |
| **Process Snapshot** | `strategies/processes.py` | Running process inventory | `ps -eo pid,ppid,user,lstart,etime,cmd --no-headers` | `processes` | `ps` |
| **Network Sockets** | `strategies/sockets.py` | Listening service discovery | `ss -tulpn` or `netstat -tulpn` | `listen_sockets` | `ss` or `netstat` |
| **OS Information** | `strategies/osinfo.py` | System identification | `/etc/os-release`, `uname -r`, `uname -m` | `os_info` | None |
| **Routing State** | `strategies/routes.py` | Network routing configuration | `ip route show`, `ip rule show`, config files | `routing_state` | `ip` |

### Planned Audit Strategies

| Strategy | Planned File | Purpose | Expected Commands | Database Tables | Priority |
|----------|-------------|---------|-------------------|-----------------|----------|
| **User Accounts** | `strategies/users.py` | Account inventory | `/etc/passwd`, `getent passwd` | `users` | High |
| **Group Management** | `strategies/groups.py` | Group membership | `/etc/group`, `getent group` | `groups` | High |
| **Login History** | `strategies/logins.py` | Authentication events | `last`, `lastb`, `journalctl` | `login_events` | Medium |
| **Shell History** | `strategies/bash_history.py` | Command history analysis | User `.bash_history` files | `bash_history` | Medium |
| **System Services** | `strategies/services.py` | Service state inventory | `systemctl list-units`, `chkconfig` | `services` | Medium |
| **Firewall State** | `strategies/firewall.py` | Security policy capture | `iptables-save`, `firewall-cmd` | `firewall_state` | Medium |
| **Network Interfaces** | `strategies/netif.py` | Interface configuration | `ip addr`, `ip link` | `net_interfaces` | Medium |
| **Resource Usage** | `strategies/resources.py` | Performance baseline | `uptime`, `free`, `df` | `resource_snapshots`, `disk_usage` | Low |
| **Hardware Info** | `strategies/hardware.py` | Physical inventory | `lspci`, `lsusb`, `lsblk` | `hw_pci`, `hw_usb`, `hw_block` | Low |
| **Network Discovery** | `strategies/nmap.py` | External service scan | `nmap` (optional) | `nmap_results` | Optional |

## Utility and Management Layer

### Database Management

| Component | File | Purpose | Key Functions | Usage |
|-----------|------|---------|---------------|---------|
| **Schema Seeder** | `scripts/seed_db.py` | Database initialization | Initialize schema, insert defaults, add sample hosts | One-time setup |
| **Configuration TUI** | `scripts/config_utility.py` | Interactive host/strategy management | Menu-driven host management, strategy enable/disable | Ongoing configuration |

### Development and Testing

| Component | Directory/File | Purpose | Coverage | Status |
|-----------|----------------|---------|----------|--------|
| **Unit Tests** | `tests/test_*.py` | Component-level testing | 0+ tests methods, >90% coverage | ✅ Complete |
| **Integration Tests** | `tests/integration/` | End-to-end workflow testing | Full audit simulation | ✅ Complete |
| **Test Fixtures** | `tests/conftest.py` | Shared test data and mocks | Database fixtures, SSH mocking, sample outputs | ✅ Complete |
| **Test Configuration** | `pytest.ini` | Test execution configuration | Markers, coverage settings, warning filters | ✅ Complete |

## Data Flow Architecture

### Session Management Flow
```
CLI Input → Orchestrator → Database Session → Host Loop → Strategy Execution → Result Storage
```

### Strategy Execution Flow
```
Strategy.probe() → Tool Availability Check → Strategy.run() → Command Execution → Data Parsing → Database Insert
```

### Error Handling Flow
```
Error Occurrence → Error Recording → Check Status Update → Continue Next Strategy/Host → Session Completion
```

## Configuration Data Flow

### Host Configuration
```sql
-- Host definition with connection parameters
hosts (id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo)
```

### Global Strategy Control
```sql
-- Global enable/disable for all strategies
global_defaults (rpm_inventory, processes, sockets, ... = 1/0)
```

### Host-Specific Overrides
```sql
-- Per-host strategy overrides
host_overrides (host_id, rpm_inventory, processes, sockets, ... = 1/0/NULL)
```

## Extension Points and APIs

### Adding New Strategies
1. **Create Strategy Class**: Inherit from `AuditCheck` in `strategies/new_strategy.py`
2. **Implement Interface**: Define `name`, `requires`, `probe()`, and `run()` methods
3. **Database Schema**: Add tables to `docs/schema.sql` if needed
4. **Register Strategy**: Update `strategies/__init__.py` (when implemented)
5. **Add Tests**: Create comprehensive unit tests in `tests/test_strategies.py`

### Extending Database Schema
1. **Update Schema**: Modify `docs/schema.sql` with new tables/columns
2. **Migration Logic**: Schema changes applied idempotently via `ensure_schema()`
3. **Strategy Updates**: Modify corresponding strategy to use new schema
4. **Test Updates**: Update fixtures and tests for new data structures

### Custom Parsers
1. **Parser Functions**: Add to `utils/parsing.py` with format-specific logic
2. **Error Handling**: Implement robust parsing with malformed data tolerance
3. **Testing**: Add parser tests with realistic and edge-case data
4. **Documentation**: Document expected input/output formats

## Dependencies and Requirements

### Python Standard Library
- `sqlite3`: Database operations
- `subprocess`: SSH command execution
- `argparse`: CLI parsing
- `hashlib`, `gzip`, `base64`: Data compression and hashing
- `shlex`: Safe command shell escaping
- `time`: Timestamp generation
- `os`: File system operations

### External Dependencies
- **pytest**: Testing framework with fixtures and mocking
- **SSH**: System SSH client for remote command execution
- **Target System Tools**: `rpm`, `ps`, `ss`/`netstat`, `ip`, etc.

### Development Dependencies
- **Linting**: ruff, black, isort, flake8, pylint, pyright
- **CI/CD**: GitHub Actions with multi-Python version testing
- **Pre-commit**: Code quality enforcement

## Security and Access Requirements

### Target System Access
- **SSH Access**: Root or sudo-capable user account
- **Network**: SSH port (22 or custom) accessibility
- **Authentication**: SSH keys (preferred) or password

### Required Sudo Commands (Future Documentation)
Commands that may require sudo elevation:
- File system access: Reading protected configuration files
- Process information: Detailed process and file descriptor access  
- Network information: Advanced routing and firewall state
- System logs: Authentication and system event logs
- Hardware information: Some hardware detection commands

### Security Posture
- **Read-Only**: No system modifications performed
- **Controlled Access**: Limited to information gathering commands
- **Local Storage**: All data remains on USB device
- **Audit Trail**: Complete command execution logging
