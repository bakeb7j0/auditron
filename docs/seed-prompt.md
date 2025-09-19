# Auditron Seed Prompt (Context Bootstrap)

You are assisting with **Auditron**, a USB-hosted, agentless auditing tool for CentOS 7.6. It SSHes into configured hosts, runs modular checks using the **Strategy pattern**, and stores configuration + results in a **SQLite** DB on the USB. Execution is **resumable**; checks are toggleable globally and per-host.

**Repo entrypoint:** `auditron.py`  
**Docs:** `docs/` (EARS requirements in `requirements-ears.md` are authoritative)  
**Plug-ins:** `strategies/*.py` each implement `probe()` + `run()` with `AuditContext`.

Internalize:
- Strategy isolation: add/modify checks without touching orchestrator.
- Resume semantics: `sessions`, `check_runs`, `errors` tables track progress.
- Data model: normalized; text/config snapshots are gzip-compressed + SHA-256 deduped.
- CentOS 7.6 tooling: `rpm`, `yum history`, `ss|netstat`, `systemctl`, `last|lastb`, `ip`, `nmcli`, etc.
- Security: read-only posture; sudo limited to read-only commands; path allow/deny for content capture; UTC normalization.

Typical tasks:
- Implement/extend strategies (e.g., firewall, nmap, hardware).
- Write robust parsers + unit tests.
- Improve resume/progress UX.
- Add reports/exporters (future).

Start by reading:
- `docs/requirements-ears.md`
- `docs/architecture.md`
- `docs/check-specs.md`
- `docs/data-model.md`
- `docs/schema.sql`