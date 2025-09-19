# Audit Check Specifications

## Overview

This document defines the complete set of audit checks (strategies) that Auditron performs on target CentOS 7.6 systems. Each check is implemented as a strategy class in the `strategies/` directory.

## Implemented Strategies

### 1. RPM Package Management

#### RPM Inventory (`strategies/rpm_inventory.py`)
- **Purpose**: Complete installed package inventory with metadata
- **Commands**: `rpm -qa --qf '%{NAME}|%{EPOCH}|%{VERSION}|%{RELEASE}|%{ARCH}|%{INSTALLTIME}\n'`
- **Requirements**: `rpm` command availability
- **Data Collected**:
  - Package name, epoch, version, release, architecture
  - Installation timestamp for change tracking
  - Complete system package baseline
- **Storage**: `rpm_packages` table
- **Use Cases**: Asset inventory, vulnerability assessment, change detection

#### RPM Verification (`strategies/rpm_verify.py`) 
- **Purpose**: Detect modified/corrupted files vs RPM database
- **Commands**: `rpm -Va --nodigest --nosignature`
- **Requirements**: `rpm` command availability
- **Data Collected**:
  - File verification flags (permissions, ownership, content)
  - File metadata (stat information)
  - Content snapshots for changed text files
- **Storage**: `rpm_verified_files`, `file_meta`, `file_snapshots` tables
- **Security Focus**: Integrity verification, unauthorized changes
- **File Snapshot Logic**:
  ```python
  # Only snapshot text files that have changed
  if changed and file_type_contains("text"):
      content = ssh.run(f"cat {path}")
      store_compressed_snapshot(content)
  ```

### 2. System Information

#### OS and Kernel Info (`strategies/osinfo.py`)
- **Purpose**: System identification and baseline information
- **Commands**: `/etc/os-release`, `uname -r`, `uname -m`
- **Requirements**: None (uses standard files/commands)
- **Data Collected**:
  - OS name, version, distribution info
  - Kernel version and architecture
  - System identification for reporting
- **Storage**: `os_info` table
- **Future**: OS detection for strategy adaptation

### 3. Network and Connectivity

#### Network Sockets (`strategies/sockets.py`)
- **Purpose**: Active network service discovery and port inventory
- **Commands**: `ss -tulpn` (preferred) or `netstat -tulpn` (fallback)
- **Requirements**: `ss` or `netstat` availability
- **Data Collected**:
  - Listening ports (TCP/UDP)
  - Process associations (PID, process name)
  - Socket states and addresses
- **Storage**: `listen_sockets` table
- **Security Focus**: Attack surface assessment, unauthorized services

#### Routing State (`strategies/routes.py`)
- **Purpose**: Network routing configuration and current state
- **Commands**: 
  - `ip route show` - Current routing table
  - `ip rule show` - Policy routing rules
  - Network configuration files in `/etc/sysconfig/network-scripts/`
  - `nmcli` NetworkManager configuration (if available)
- **Requirements**: `ip` command availability
- **Data Collected**:
  - Current routing table snapshot
  - Policy routing rules
  - Static route configurations
  - NetworkManager connection profiles
- **Storage**: `routing_state` table with content type separation
- **Configuration Capture**:
  ```bash
  # Route files
  /etc/sysconfig/network-scripts/route-*
  
  # Interface configs (routing-relevant lines)
  /etc/sysconfig/network-scripts/ifcfg-* 
  
  # NetworkManager profiles
  nmcli connection show
  ```

### 4. Process and Service Management

#### Running Processes (`strategies/processes.py`)
- **Purpose**: Complete process inventory with hierarchy and timing
- **Commands**: `ps -eo pid,ppid,user,lstart,etime,cmd --no-headers`
- **Requirements**: `ps` command availability
- **Data Collected**:
  - Process ID and parent process ID
  - Executing user account
  - Process start time and elapsed time
  - Complete command line with arguments
- **Storage**: `processes` table
- **Security Applications**: Unauthorized processes, privilege analysis
- **Future Enhancement**: Open files per process (`proc_open_files` table)

### 5. Planned/Future Strategies

#### User and Group Management
- **Purpose**: Account inventory and privilege mapping
- **Commands**: `/etc/passwd`, `/etc/group`, `getent`
- **Data**: User accounts, group memberships, home directories, shells
- **Storage**: `users`, `groups` tables

#### Authentication and Access
- **Purpose**: Login history and authentication events
- **Commands**: `last`, `lastb`, `journalctl` (auth events)
- **Data**: Successful/failed logins, session duration, source IPs
- **Storage**: `login_events` table

#### Shell History Analysis  
- **Purpose**: Command history forensics and usage patterns
- **Commands**: User `.bash_history` files, shell configuration
- **Data**: Historical commands, timestamps, user attribution
- **Storage**: `bash_history` table
- **Privacy**: Configurable depth, sensitive command filtering

#### System Services
- **Purpose**: Service inventory and startup configuration
- **Commands**: `systemctl list-units`, `chkconfig --list` (legacy)
- **Data**: Service states, enable status, dependencies
- **Storage**: `services` table

#### Network Discovery (Optional)
- **Purpose**: Network topology and host discovery
- **Commands**: `nmap` (when available and enabled)
- **Data**: Network scan results, service discovery
- **Storage**: `nmap_results` table (XML format)
- **Considerations**: Performance impact, security concerns

#### System Resources
- **Purpose**: Performance baseline and resource utilization
- **Commands**: `uptime`, `free`, `df`, `/proc/meminfo`
- **Data**: Load averages, memory usage, disk space
- **Storage**: `resource_snapshots`, `disk_usage` tables

#### Firewall Configuration
- **Purpose**: Security policy and rule inventory
- **Commands**: `iptables-save`, `firewall-cmd --list-all`
- **Data**: Firewall rules, zones, services, policies
- **Storage**: `firewall_state` table

#### Network Interfaces
- **Purpose**: Network configuration and addressing
- **Commands**: `ip addr`, `ip link`, interface configuration files
- **Data**: Interface states, addresses, MTU, MAC addresses
- **Storage**: `net_interfaces` table

#### Hardware Inventory
- **Purpose**: Physical system inventory and diagnostics
- **Commands**: `lspci`, `lsusb`, `lsblk`, `/proc/cpuinfo`
- **Data**: PCI devices, USB devices, block devices, CPU info
- **Storage**: `hw_pci`, `hw_usb`, `hw_block` tables

## Strategy Implementation Pattern

### Standard Strategy Structure
```python
class ExampleCheck(AuditCheck):
    name = "example"                    # Database identifier
    requires = ("tool1", "tool2")       # Required system tools
    
    def probe(self, ctx: AuditContext) -> bool:
        """Verify required tools are available"""
        return all(ctx.ssh.which(tool) for tool in self.requires)
    
    def run(self, ctx: AuditContext) -> None:
        """Execute audit check with error handling"""
        cid = start_check(ctx.db, ctx.session_id, ctx.host["id"], self.name)
        try:
            # Execute commands and collect data
            result = ctx.ssh.run("command")
            
            # Parse and store results
            for record in parse_output(result.out):
                ctx.db.execute("INSERT INTO table ...", record)
            
            ctx.db.commit()
            mark_check(ctx.db, cid, "SUCCESS", None)
        except Exception as e:
            record_error(ctx.db, cid, "run", str(e), -1)
            mark_check(ctx.db, cid, "ERROR", str(e))
```

### Error Handling Standards
- **Tool Availability**: Probe phase catches missing dependencies
- **Command Failures**: Capture exit codes and stderr in error table
- **Parsing Errors**: Continue with partial data, log parsing issues
- **Database Errors**: Transaction rollback, error recording
- **Network Issues**: Timeout handling, connection retry logic

### Data Collection Principles
- **Read-Only Operations**: No system modifications
- **Snapshot Consistency**: UTC timestamps for temporal correlation
- **Content Deduplication**: SHA-256 hashing prevents duplicate storage
- **Compression**: Gzip for large text content (configs, logs)
- **Size Limits**: Configurable caps on snapshot sizes

### Performance Considerations
- **Command Efficiency**: Minimize exec calls, batch operations
- **Network Optimization**: Reuse SSH connections, avoid chatty protocols
- **Storage Efficiency**: Compression, deduplication, normalized schema
- **Resource Limits**: Configurable timeouts and size constraints

### Security Constraints
- **Privilege Requirements**: Document required sudo commands
- **Path Restrictions**: Allow-list for file system access
- **Content Filtering**: Avoid capturing sensitive data (passwords, keys)
- **Audit Trail**: Complete logging of executed commands

## Configuration and Control

### Global Enable/Disable
Each strategy can be globally enabled/disabled via `global_defaults` table:
```sql
UPDATE global_defaults SET rpm_inventory = 0 WHERE id = 1;  -- Disable globally
```

### Per-Host Overrides
Host-specific strategy control via `host_overrides` table:
```sql
INSERT INTO host_overrides (host_id, nmap, max_snapshot_bytes) 
VALUES (1, 0, 1048576);  -- Disable nmap, limit snapshots for host 1
```

### Resource Limits
- `max_snapshot_bytes`: Maximum file snapshot size
- `command_timeout_sec`: Per-command timeout
- `gzip_snapshots`: Enable/disable compression

## Future Enhancements

### Multi-OS Support
- OS detection in probe phase
- Command adaptation based on OS/version
- Distribution-specific strategy variants

### Incremental Auditing
- Change detection between audit runs
- Delta reporting and analysis
- Baseline establishment and drift detection

### Advanced Network Discovery
- Service fingerprinting and version detection
- Vulnerability scanning integration
- Network topology mapping

### Performance Optimization
- Parallel strategy execution (where safe)
- Streaming data processing for large outputs
- Background compression and storage
