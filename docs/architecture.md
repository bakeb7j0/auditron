# Architecture & Execution

```
[ CLI ] → Orchestrator → HostRunner (SSH) → Strategy Manager → [Check Strategies]
                                      ↓
                               Result Writer (SQLite)
                                      ↓
                                  Resume Manager
                                      ↓
                                   Logger/Progress
```

## Components
- **Orchestrator:** Manages sessions, iterates hosts and enabled strategies.
- **HostRunner (SSH):** Paramiko wrapper with `sudo`, timeouts, `which()` cache.
- **Strategy Manager:** Registry of check plug‑ins; probes prerequisites; SKIP with reason if unmet.
- **Result Writer:** Normalized inserts; content gzip + SHA‑256 dedupe.
- **Resume Manager:** Tracks `check_runs` to continue after interruption.
- **Logger/Progress:** TTY progress bars (tqdm/rich) with plain‑text fallback.

## Strategy Pattern (Python)
```python
from abc import ABC, abstractmethod

class AuditContext:
    def __init__(self, host, ssh, db, limits, clock):
        self.host = host; self.ssh = ssh; self.db = db
        self.limits = limits; self.clock = clock

class AuditCheck(ABC):
    name: str = "base"
    requires: tuple[str, ...] = ()

    @abstractmethod
    def probe(self, ctx: AuditContext) -> bool: ...
    @abstractmethod
    def run(self, ctx: AuditContext) -> None: ...
```

Plug‑ins register in a simple registry; orchestrator loops `probe()` then `run()` for enabled checks.

## Execution & Resume
1. Open DB; create schema if needed. Detect last `finished_at IS NULL` session.
2. Prompt: **resume** previous vs **start new**.
3. For each host (serial): evaluate overrides; for each strategy → `probe()` or SKIP; then `run()` and persist.
4. Each `check_runs` row set atomically; errors recorded in `errors` table.

## Progress UX
- Overall: `Host i/N: <host> — completed/enabled [SUCCESS:x SKIP:y ERROR:z]`
- Per‑check: `▶ rpm_inventory … ✓`, `↷ sockets … SKIP (ss not found)`, `✗ processes … ERROR (timeout)`
