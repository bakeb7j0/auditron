# Command Line Interface

## Basic Usage

### Starting Fresh Audit
```bash
# Start new audit session (deletes any unfinished session)
python auditron.py --fresh
python auditron.py fresh        # Positional argument (legacy)

# Specify custom database location
python auditron.py --fresh --db /path/to/custom.db
```

### Resuming Interrupted Audit
```bash
# Resume last unfinished session
python auditron.py --resume
python auditron.py resume       # Positional argument (legacy)

# Resume with custom database
python auditron.py --resume --db /path/to/custom.db
```

## Command Line Arguments

### Core Arguments
- `--fresh` / `fresh`: Start new audit session (maps to database mode 'new')
- `--resume` / `resume`: Resume interrupted session from database
- `--db PATH`: SQLite database file path (default: `auditron.db`)

### Argument Validation
- Mutually exclusive: Cannot specify both `--fresh` and `--resume`
- Conflict detection: Positional and flag arguments cannot conflict
- Required mode: Must specify either fresh or resume operation

### Examples with Error Handling
```bash
# Valid usage
python auditron.py --fresh
python auditron.py --resume
python auditron.py fresh
python auditron.py resume

# Invalid usage (will error)
python auditron.py --fresh --resume  # Mutually exclusive
python auditron.py fresh --resume    # Conflicting modes
python auditron.py                   # No mode specified
```

## Database Session Modes

### Fresh Mode (`--fresh`)
- Creates new session in database with mode 'new'
- Processes all configured hosts from beginning
- Any existing unfinished session is abandoned
- Use when starting audit from scratch

### Resume Mode (`--resume`)
- Finds most recent unfinished session
- Continues execution from last completed host/strategy
- Preserves all previously collected data
- Reports "No unfinished session found" if none exists

## Current Limitations (MVP)

### Missing CLI Features (Future Development)
The current implementation does not support:

```bash
# Host filtering (planned)
python auditron.py --host 10.0.0.12
python auditron.py --hosts host1,host2,host3

# Strategy selection (planned)
python auditron.py --skip nmap,file_snapshots
python auditron.py --only rpm_inventory,processes

# Timeout overrides (planned)
python auditron.py --timeout 45
python auditron.py --strategy-timeout 30

# Verbosity control (planned)
python auditron.py --verbose
python auditron.py --quiet
python auditron.py --progress

# Output control (planned)
python auditron.py --report-format html
python auditron.py --output-dir /tmp/audit-results
```

### Current Workarounds
For features not yet in CLI:

**Host Management**: Use configuration utility
```bash
python scripts/config_utility.py
# Interactive menu to add/remove/configure hosts
```

**Strategy Control**: Database configuration
```bash
# Disable strategy globally
sqlite3 auditron.db "UPDATE global_defaults SET nmap = 0 WHERE id = 1;"

# Disable for specific host
sqlite3 auditron.db "INSERT INTO host_overrides (host_id, nmap) VALUES (1, 0);"
```

**Timeout Configuration**: Database settings
```bash
sqlite3 auditron.db "UPDATE global_defaults SET command_timeout_sec = 45 WHERE id = 1;"
```

## Environment Setup

### Python Environment
```bash
# Create virtual environment
python3 -m venv auditron-env
source auditron-env/bin/activate  # Linux/Mac
# auditron-env\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Database Initialization
```bash
# Initialize database schema and defaults
python scripts/seed_db.py auditron.db

# Add target hosts interactively
python scripts/config_utility.py auditron.db
```

### SSH Setup
Ensure target systems are accessible:
```bash
# Test SSH connectivity
ssh -o BatchMode=yes root@target-host "echo 'Connection successful'"

# Setup SSH keys (recommended)
ssh-copy-id root@target-host

# Verify sudo access (if needed)
ssh root@target-host "sudo -n whoami"
```

## Execution Workflow

### Standard Audit Process
1. **Preparation**
   ```bash
   cd /path/to/auditron
   source auditron-env/bin/activate
   ```

2. **Host Configuration**
   ```bash
   python scripts/config_utility.py auditron.db
   # Add target hosts with credentials
   ```

3. **Execute Audit**
   ```bash
   python auditron.py --fresh
   # Monitor progress and handle any errors
   ```

4. **Handle Interruptions**
   ```bash
   # If interrupted, resume with:
   python auditron.py --resume
   ```

5. **Export Results** (manual process currently)
   ```bash
   # Copy database for analysis
   cp auditron.db results/audit-$(date +%Y%m%d).db
   ```

### Progress Monitoring
Currently minimal progress feedback. Look for:
- Database `check_runs` table for completion status
- Console output for errors and basic progress
- Log files (if configured)

**Future**: Rich progress bars, real-time status, estimated completion

## Error Handling and Recovery

### Common Issues

**SSH Connection Failures**:
```bash
# Debug SSH connectivity
ssh -v root@target-host

# Check SSH configuration
cat ~/.ssh/config
```

**Database Lock Issues**:
```bash
# Check for competing processes
ps aux | grep auditron

# Remove lock file if safe
rm auditron.db-journal  # Only if no auditron processes running
```

**Incomplete Sessions**:
```bash
# Check session status
sqlite3 auditron.db "SELECT * FROM sessions ORDER BY id DESC LIMIT 1;"

# Resume incomplete session
python auditron.py --resume
```

### Exit Codes
- `0`: Successful completion
- `1`: General error (check console output)
- `2`: Command line argument error
- Other codes: System-specific errors

## Development and Testing

### Local Development
```bash
# Run with test database
python auditron.py --fresh --db test.db

# Reset test environment
rm test.db
python scripts/seed_db.py test.db
```

### Debugging
```bash
# Enable verbose logging (manual implementation needed)
export AUDITRON_DEBUG=1
python auditron.py --fresh

# Direct database inspection
sqlite3 auditron.db
.schema
SELECT * FROM sessions;
SELECT * FROM check_runs WHERE status = 'ERROR';
```
