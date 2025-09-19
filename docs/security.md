# Security & Privacy Model

## Security Architecture Overview

Auditron implements a defense-in-depth security model designed to minimize risk while collecting comprehensive audit data from target systems. The architecture prioritizes data integrity, system safety, and privacy protection.

## Read-Only Security Posture

### Core Principle
Auditron operates under a **strict read-only mandate** - no system modifications are performed on target hosts.

### Implementation
- **Command Selection**: Only information-gathering commands are executed
- **No Write Operations**: No file creation, modification, or deletion
- **No Service Changes**: No daemon starts/stops, configuration changes, or reboots
- **No User Management**: No account creation, password changes, or privilege modifications
- **Audit Trail**: Complete logging of all executed commands for verification

### Verification Mechanisms
```python
# Example: Read-only command patterns
SAFE_COMMANDS = [
    "rpm -qa",           # Package listing
    "ps -eo",            # Process information
    "ss -tulpn",         # Socket information
    "cat /etc/os-release", # System information
    "ip route show",     # Network configuration
]

# Commands that require careful review
SUDO_READ_COMMANDS = [
    "cat /var/log/secure",     # Authentication logs
    "iptables-save",           # Firewall rules
    "cat /etc/shadow",         # Password file (hashes only)
]
```

## Privilege Management

### Current Implementation (MVP)
- **Root Access**: Currently designed to run as root via SSH
- **Rationale**: Simplifies access to system information and configuration files
- **Risk Mitigation**: Read-only command restriction, comprehensive audit logging

### Sudo Command Requirements
Commands that require elevated privileges (future privilege separation):

#### System Configuration Access
```bash
# Network configuration
sudo cat /etc/sysconfig/network-scripts/*
sudo iptables-save
sudo firewall-cmd --list-all

# System logs
sudo cat /var/log/secure
sudo cat /var/log/messages
sudo journalctl --since="1 day ago"

# Authentication data
sudo cat /etc/shadow          # Password hashes only
sudo cat /etc/sudoers
sudo cat /etc/ssh/sshd_config
```

#### Process and Resource Information
```bash
# Process details with file descriptors
sudo lsof -p <pid>
sudo cat /proc/<pid>/environ

# System resource access
sudo cat /proc/meminfo
sudo cat /proc/cpuinfo
```

#### Hardware and Device Information
```bash
# Hardware enumeration
sudo lspci -v
sudo lsusb -v
sudo dmidecode

# Block device information
sudo lsblk -f
sudo fdisk -l
```

### Future Privilege Separation Model
```bash
# Planned: Minimal privilege user with specific sudo rules
# /etc/sudoers.d/auditron:
auditron ALL=(root) NOPASSWD: /bin/cat /etc/shadow
auditron ALL=(root) NOPASSWD: /sbin/iptables-save
auditron ALL=(root) NOPASSWD: /bin/journalctl --since=*
# ... additional read-only commands as needed
```

## Data Protection and Privacy

### Sensitive Data Handling

#### Content Filtering
```python
# Avoid capturing sensitive patterns
SENSITIVE_PATTERNS = [
    r'password\s*=\s*\S+',      # Configuration passwords
    r'key\s*=\s*[A-Za-z0-9+/=]+',  # API keys, certificates
    r'token\s*=\s*\S+',        # Authentication tokens
    r'secret\s*=\s*\S+',       # Secret values
]

# File paths to avoid or sanitize
SENSITIVE_PATHS = [
    '/etc/shadow',              # Only hashes, not full content
    '/home/*/.ssh/id_*',        # SSH private keys
    '/etc/ssl/private/*',       # SSL private keys
    '/var/log/audit/audit.log', # May contain sensitive command args
]
```

#### Snapshot Size Controls
```sql
-- Configurable limits in global_defaults table
max_snapshot_bytes INTEGER DEFAULT 524288,  -- 512KB limit
gzip_snapshots INTEGER DEFAULT 1,          -- Enable compression
```

#### Allow-List File Patterns
```python
# Only capture configuration files matching safe patterns
ALLOWED_CONFIG_GLOBS = [
    '/etc/*.conf',
    '/etc/sysconfig/*',
    '/etc/systemd/system/*.service',
    '/etc/network/interfaces*',
    '/etc/hosts',
    '/etc/resolv.conf',
]

# Explicitly blocked patterns
BLOCKED_GLOBS = [
    '/etc/shadow*',             # Password files
    '/etc/ssl/private/*',       # Private keys
    '/home/*/.ssh/id_*',        # SSH private keys
    '/etc/pki/private/*',       # Certificate private keys
]
```

### Data Integrity and Deduplication

#### Content Hashing
```python
# SHA-256 hashing for content verification and deduplication
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# Prevent duplicate storage of identical content
if sha256_hash not in existing_snapshots:
    store_compressed_snapshot(content, sha256_hash)
```

#### Compression Strategy
```python
# Gzip compression for text content
def gz_bytes(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=6)

# Storage optimization
compressed_size = len(gz_bytes(content))
if compressed_size < len(content) * 0.8:  # 20% compression threshold
    store_compressed(gz_bytes(content))
else:
    store_uncompressed(content)
```

## Network Security

### SSH Connection Security

#### Connection Parameters
```python
# Secure SSH client configuration
ssh_options = [
    "-o", "BatchMode=yes",          # No interactive prompts
    "-o", "StrictHostKeyChecking=ask", # Verify host keys
    "-o", "UserKnownHostsFile=~/.ssh/known_hosts",
    "-o", "ConnectTimeout=10",       # Connection timeout
    "-o", "ServerAliveInterval=30",  # Keep-alive
]
```

#### Authentication Methods
```python
# SSH key authentication (preferred)
if host.get("ssh_key_path"):
    ssh_cmd += ["-i", host["ssh_key_path"]]

# Password authentication (fallback)
# Note: Requires sshpass or similar for automation
# Better: Use SSH agent or key-based auth
```

### Network Traffic Minimization
```python
# Command batching to reduce SSH overhead
batch_commands = [
    "rpm -qa --qf '%{NAME}|%{VERSION}|%{RELEASE}\n'",
    "ps -eo pid,ppid,user,cmd --no-headers",
    "ss -tulpn",
]
result = ssh.run(" && ".join(batch_commands))
```

## Temporal Security

### UTC Timestamp Normalization
```python
# Consistent timestamp format across all data
def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# All database timestamps use UTC
INSERT INTO table (captured_at) VALUES (?)  -- UTC timestamp
```

### Audit Session Tracking
```sql
-- Complete audit trail with session correlation
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,    -- UTC start time
    finished_at TEXT,            -- UTC completion time
    mode TEXT CHECK (mode IN ('new','resume'))
);

-- Individual check execution tracking
CREATE TABLE check_runs (
    session_id INTEGER NOT NULL,
    host_id INTEGER NOT NULL,
    check_name TEXT NOT NULL,
    started_at TEXT,             -- UTC start time
    finished_at TEXT,            -- UTC completion time
    status TEXT CHECK (status IN ('SUCCESS','SKIP','ERROR'))
);
```

## Logging and Audit Trail

### Command Execution Logging
```python
# Complete command audit trail
class SSHClient:
    def run(self, command: str) -> SSHResult:
        # Log command execution with timestamp
        log_entry = {
            "timestamp": ts(),
            "host": self.host["hostname"],
            "user": self.host["ssh_user"],
            "command": command,
            "exit_code": None  # Filled after execution
        }
        
        # Execute and log results
        result = self._execute_ssh(command)
        log_entry["exit_code"] = result.rc
        
        # Store in audit log
        self._log_command(log_entry)
        return result
```

### Error Recording
```sql
-- Comprehensive error tracking
CREATE TABLE errors (
    check_run_id INTEGER NOT NULL,
    stage TEXT,                  -- 'probe', 'run', 'parse'
    stderr TEXT,                 -- Command error output
    exit_code INTEGER           -- Command exit status
);
```

### Secret Avoidance in Logs
```python
# Sanitize commands before logging
def sanitize_command(cmd: str) -> str:
    # Remove potential passwords from logged commands
    sanitized = re.sub(r'password=[^\s]+', 'password=***', cmd)
    sanitized = re.sub(r'-p\s+\S+', '-p ***', sanitized)
    return sanitized
```

## Data Storage Security

### Local Storage Only
- **USB-Based**: All data remains on local USB device
- **No Network Storage**: No cloud or network file system usage
- **Physical Security**: USB device security is operator responsibility
- **Encryption Consideration**: Future disk encryption for USB device

### Database Security
```python
# SQLite security measures
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys=ON;")     # Referential integrity
conn.execute("PRAGMA journal_mode=WAL;")    # Write-ahead logging
conn.execute("PRAGMA synchronous=FULL;")    # Durability
```

### File Permission Restrictions
```bash
# Secure file permissions for audit database
chmod 600 auditron.db          # Owner read/write only
chmod 700 auditron/            # Directory access control
```

## Compliance and Regulatory Considerations

### Data Retention
- **Local Control**: All data retention controlled by operator
- **No Automatic Deletion**: Audit data preserved until manually removed
- **Export Capability**: Data can be exported for long-term archival

### Access Control
- **Physical Access**: USB device controls access to audit data
- **Operator Authentication**: System-level authentication for audit execution
- **Data Separation**: Each audit session creates separate data set

### Privacy Protection
- **No Personal Data**: Focus on system configuration, not user data
- **Minimal User Information**: Only system accounts and login patterns
- **Sanitized Snapshots**: Content filtering for sensitive information

## Risk Assessment and Mitigation

### Identified Risks

#### High Risk (Mitigated)
- **Unauthorized System Changes**: Mitigated by read-only command restriction
- **Credential Exposure**: Mitigated by SSH key usage and secure logging
- **Data Exfiltration**: Mitigated by local-only storage model

#### Medium Risk (Managed)
- **Network Eavesdropping**: Managed by SSH encryption
- **Privilege Escalation**: Managed by controlled sudo usage
- **System Performance Impact**: Managed by command timeouts and resource limits

#### Low Risk (Monitored)
- **USB Device Loss**: Physical security responsibility
- **Database Corruption**: Monitored via transaction integrity
- **Command Injection**: Monitored via command sanitization

### Security Validation
```python
# Regular security validation checks
def validate_security_posture():
    # Verify no write operations in command history
    assert no_write_commands_executed()
    
    # Verify sensitive data filtering
    assert no_sensitive_data_in_snapshots()
    
    # Verify proper privilege usage
    assert sudo_usage_within_policy()
```

## Future Security Enhancements

### Planned Improvements
1. **Privilege Separation**: Move from root access to limited sudo model
2. **USB Encryption**: Full disk encryption for audit database
3. **Command Whitelisting**: Explicit approval for all executed commands
4. **Real-time Monitoring**: Live security policy validation
5. **Audit Report Sanitization**: Automated sensitive data removal

### Security Development Process
- **Threat Modeling**: Regular security architecture review
- **Penetration Testing**: Security validation of audit process
- **Code Review**: Security-focused code review for all changes
- **Compliance Verification**: Regular compliance posture assessment
