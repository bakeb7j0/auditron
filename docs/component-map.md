# Auditron Python Component Map

| Filepath               | Component                      | Purpose                                                                 | Dependencies                                  |
|-------------------------|--------------------------------|-------------------------------------------------------------------------|-----------------------------------------------|
| `auditron.py`          | Orchestrator / CLI             | Main entry point; parses CLI args; loads hosts; runs strategies; manages sessions. | `utils/db.py`, `utils/ssh_runner.py`, `strategies/*` |
| `utils/db.py`          | Database utilities             | Connect to SQLite, enforce schema, manage sessions, check_runs, inserts. | `docs/schema.sql`                             |
| `utils/ssh_runner.py`  | SSH client wrapper             | Provides `run()` to execute commands over SSH; caches `which` checks.   | `subprocess`                                  |
| `utils/parsing.py`     | Output parsers                 | Parse outputs (e.g., `rpm -Va`, `ss`) into structured tuples.            | none                                          |
| `utils/compress.py`    | Compression + hashing          | Gzip content, compute SHA256; used for file snapshots.                  | `hashlib`, `gzip`                             |
| `strategies/base.py`   | Strategy interface             | Defines `AuditContext` and abstract `AuditCheck` base class.            | none                                          |
| `strategies/__init__.py` | Registry                      | Imports all strategies and builds `REGISTRY` for orchestration.          | Each strategy module                          |
| `strategies/rpm_inventory.py` | Installed RPMs audit-check | Collects full installed RPM list with metadata.                         | `utils/db.py`                                 |
| `strategies/rpm_verify.py`    | RPM verification audit-check | Captures changed/removed files vs RPM DB; stores metadata + snapshots.   | `utils/parsing.py`, `utils/compress.py`, `utils/db.py` |
| `strategies/processes.py`     | Processes audit-check       | Snapshots running processes with PID, PPID, start time, command.         | `utils/db.py`                                 |
| `strategies/sockets.py`       | Sockets audit-check         | Captures listening sockets via `ss` or `netstat`.                        | `utils/parsing.py`, `utils/db.py`             |
| `strategies/osinfo.py`        | OS/kernel audit-check       | Collects OS release + kernel info.                                      | `utils/db.py`                                 |
| `strategies/routes.py`        | Routing audit-check         | Captures current and configured routing tables.                         | `utils/db.py`                                 |
| `scripts/seed_db.py`    | DB seeding utility             | Initializes schema, inserts defaults, adds hosts from CLI.              | `docs/schema.sql`, `utils/db.py`              |
| `scripts/config_utility.py` | TUI config manager         | Menu-driven console tool to manage hosts and toggle checks.             | `utils/db.py`                                 |
| `tests/` (various)      | Unit tests                    | Covers utils and strategy modules.                                      | pytest, corresponding modules                 |

---

📌 **Note**: This table is a *planning map*; actual implementation may extend with more strategies (e.g., firewall, services, hardware) as we progress.
