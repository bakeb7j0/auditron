# Auditron Implementation Plan (One Component at a Time)

We will implement Auditron incrementally, one component per commit, in the following order.  
This ensures the foundations (DB, utils) are ready before higher-level strategies and the CLI.

---

## Phase 1 — Foundations
1. **`utils/db.py`**  
   - Database connection, schema bootstrap, session + check bookkeeping.  
   - Depends on `docs/schema.sql`.

2. **`utils/ssh_runner.py`**  
   - SSH wrapper with command execution, sudo support, and binary detection.

3. **`utils/parsing.py`**  
   - Parsers for command output (`rpm -Va`, `ss`, etc).  
   - No external deps beyond stdlib.

4. **`utils/compress.py`**  
   - Gzip compression + SHA256 helpers.  
   - Used by snapshotting in strategies.

---

## Phase 2 — Strategy Base + Registry
5. **`strategies/base.py`**  
   - `AuditContext`, abstract `AuditCheck` base with `probe()` + `run()`.

6. **`strategies/__init__.py`**  
   - Central registry `REGISTRY` of all strategies.

---

## Phase 3 — Core Strategies
7. **`strategies/osinfo.py`**  
   - Collect OS + kernel version info.  
   - Low-risk, simple.

8. **`strategies/rpm_inventory.py`**  
   - Enumerate installed RPM packages.  
   - Depends on `utils/db.py`.

9. **`strategies/rpm_verify.py`**  
   - File verification vs RPM DB, metadata, snapshots.  
   - Depends on `utils/parsing.py`, `utils/compress.py`.

10. **`strategies/processes.py`**  
    - Snapshot of running processes.  
    - Depends on `utils/db.py`.

11. **`strategies/sockets.py`**  
    - Capture listening sockets (via `ss` or `netstat`).  
    - Depends on `utils/parsing.py`.

12. **`strategies/routes.py`**  
    - Capture current + configured routing tables.  
    - Depends on `utils/db.py`.

---

## Phase 4 — Orchestration
13. **`auditron.py`**  
    - Main CLI orchestration, session handling, host iteration, resume logic.  
    - Depends on all utils + strategies.

---

## Phase 5 — Tooling & Utilities
14. **`scripts/seed_db.py`**  
    - Initialize DB schema + insert defaults + add hosts.

15. **`scripts/config_utility.py`**  
    - Console menu for host/override management.

---

## Phase 6 — Tests
16. **`tests/` suite**  
    - Unit tests for utils and strategies.  
    - Pytest-based.

---

✅ Each step will be delivered as a self-contained `mash-it.sh` with:  
- The new component’s file(s).  
- Updates to README/doc links.  
- A DCO-signed commit.

We will **not** skip ahead: one component at a time, building upward from the foundations.
