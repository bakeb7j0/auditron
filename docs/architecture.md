# Auditron Architecture

## System Design Overview

Auditron follows a layered architecture with clear separation of concerns between orchestration, execution, data collection, and persistence.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Parser    │───▶│   Orchestrator   │───▶│  Session Mgmt   │
│  (auditron.py)  │    │  (auditron.py)   │    │   (utils/db.py) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Host Iterator  │
                       │  (serial loop)   │
                       └──────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SSH Client    │◀───│  Strategy Runner │───▶│ Result Storage  │
│(utils/ssh_*.py) │    │ (strategies/*.py)│    │   (SQLite DB)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Data Parsers   │
                       │(utils/parsing.py)│
                       └──────────────────┘
```

## Component Architecture

### 1. Orchestrator Layer (`auditron.py`)

**Responsibilities**:
- CLI argument parsing and validation
- Session lifecycle management (new/resume)
- Host iteration and context creation
- High-level error handling and recovery

**Key Functions**:
- `parse_cli()` - Handle --fresh/--resume flags with backward compatibility
- `run_mode()` - Execute new audit session
- `run_resume()` - Continue interrupted session
- `run_all_checks()` - Serial strategy execution

**Session Management**:
```python
# New session workflow
session_id = db.new_session(conn, "new")
for host in hosts:
    ctx = AuditContext(host, ssh, db, limits, clock, session_id)
    run_all_checks(ctx)
db.finish_session(conn, session_id)

# Resume workflow  
session_id = db.get_unfinished_session(conn)
# Continue from where left off
```

### 2. SSH Execution Layer (`utils/ssh_runner.py`)

**SSHClient Class**:
- Connection management with timeout handling
- Command execution with sudo elevation support
- Tool availability caching (`which` command results)
- Error handling and result wrapping

**Key Features**:
- Batch mode SSH (no interactive prompts)
- Configurable timeouts (default 60s)
- SSH key or password authentication support
- Command result encapsulation (rc, stdout, stderr)

```python
class SSHResult:
    def __init__(self, rc: int, out: str, err: str):
        self.rc = rc      # Exit code
        self.out = out    # Standard output
        self.err = err    # Standard error
```

### 3. Strategy Execution Layer (`strategies/`)

**Base Strategy Interface** (`strategies/base.py`):
```python
class AuditCheck(ABC):
    name: str = "base"                    # Strategy identifier
    requires: tuple[str, ...] = ()        # Required system tools
    
    def probe(self, ctx: AuditContext) -> bool:  # Tool availability check
    def run(self, ctx: AuditContext) -> None:    # Main execution logic
```

**AuditContext** - Execution context passed to strategies:
- `host`: Target host configuration (IP, credentials, settings)
- `ssh`: SSH client instance for command execution
- `db`: Database connection for result storage
- `session_id`: Current audit session identifier
- `limits`: Configuration limits and timeouts
- `clock`: Time source (for testing/mocking)

**Strategy Lifecycle**:
1. **Probe Phase**: Verify required tools exist (`ctx.ssh.which(tool)`)
2. **Execution Phase**: Run audit commands and collect data
3. **Parsing Phase**: Structure command output into database records
4. **Storage Phase**: Insert results with error tracking

### 4. Data Persistence Layer (`utils/db.py`)

**Database Operations**:
- Connection management with foreign key enforcement
- Schema initialization and migration
- Session and check run tracking
- Error recording and status management

**Key Functions**:
- `start_check()` - Initialize check run tracking
- `mark_check()` - Update check status (SUCCESS/ERROR/SKIP)
- `record_error()` - Log execution errors with context
- Session management (new/resume/finish)

**Transaction Management**:
- Each strategy commits its own transaction
- Error recovery allows partial completion
- Resume capability preserves completed work

### 5. Data Processing Layer (`utils/`)

**Command Output Parsing** (`utils/parsing.py`):
- Structured parsing of command outputs
- Format-specific parsers (RPM, process lists, socket info)
- Error-tolerant parsing with malformed data handling

**Compression and Deduplication** (`utils/compress.py`):
- Gzip compression for large text snapshots
- SHA-256 hashing for content deduplication
- Base64 encoding for binary storage in SQLite

## Execution Flow

### Normal Execution Path
1. Parse CLI arguments and determine mode (fresh/resume)
2. Connect to SQLite database and ensure schema
3. Create or retrieve session identifier
4. Iterate through configured hosts (serial execution)
5. For each host:
   a. Create SSH client and audit context
   b. Execute all enabled strategies in sequence
   c. Each strategy: probe → run → parse → store
6. Mark session as complete

### Resume Execution Path
1. Find unfinished session in database
2. Continue host iteration from where interrupted
3. Strategy-level resume (no mid-strategy resume currently)
4. Complete remaining work and finish session

### Error Handling Strategy
- **Strategy Failure**: Log error, continue with next strategy
- **Host Failure**: Log error, continue with next host
- **Critical Failure**: Abort with error logging
- **Network Issues**: Timeout handling with retry potential

## Performance Characteristics

**Current Implementation**:
- **Host Processing**: Fully serial (one host at a time)
- **Strategy Execution**: Serial within each host
- **Network Efficiency**: Connection reuse per host
- **Storage**: Immediate persistence with transaction batching

**Future Enhancements**:
- **Multi-Host Parallelism**: Thread pool for concurrent host processing
- **Strategy Optimization**: Parallel strategy execution where safe
- **Progress Reporting**: Rich/tqdm integration for user feedback

## Security Architecture

**Read-Only Posture**:
- Commands designed for information gathering only
- No system modification capabilities
- Controlled sudo usage for privileged information access

**Data Protection**:
- Local storage only (no network transmission of results)
- Compression and deduplication to minimize storage footprint
- UTC timestamp normalization for consistency

**Access Control**:
- SSH key or password authentication
- Configurable user accounts (currently root-focused)
- Future: Principle of least privilege implementation

## Configuration Management

**Database-Driven Configuration**:
- Host definitions with connection parameters
- Global default settings for all audit checks
- Per-host overrides for specific requirements
- Strategy enable/disable at global and host level

**Runtime Configuration**:
- Command timeouts and resource limits
- Snapshot size limits and compression settings
- SSH connection parameters and authentication

## Extension Points

**Adding New Strategies**:
1. Create new class in `strategies/` inheriting from `AuditCheck`
2. Implement `probe()` and `run()` methods
3. Add corresponding database table(s) if needed
4. Register in `strategies/__init__.py`
5. Add comprehensive unit tests

**Modifying Data Model**:
1. Update `docs/schema.sql` with new tables/columns
2. Schema changes are applied idempotently via `ensure_schema()`
3. Update corresponding strategy code
4. Add database migration logic if needed

**Integration Points**:
- Custom parsers in `utils/parsing.py`
- Additional SSH client capabilities
- New compression or storage formats
- Alternative database backends (future)
