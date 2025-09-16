# Auditron Seed Prompt (Context Bootstrap)

You are assisting with **Auditron**, a USB-hosted, agentless auditing tool for CentOS 7.6 fleets. It SSHes into configured hosts, runs a modular set of checks (Strategy pattern), and stores configuration + results in a SQLite DB on the USB. Sessions are resumable; all checks are toggleable globally and per-host.

## Repository
- Root: this repository (assume you can view files under `docs/`, `strategies/`, `utils/`, `scripts/`).
- Entrypoint: `auditron.py`
- Docs index: see `README.md` and all details under `docs/` (requirements, architecture, check specs, ERD, schema, ops, security, test plan).

## What you MUST internalize
1. **Strategy Pattern:** each audit check is a self-contained plug-in (`strategies/*.py`) implementing `probe()` and `run()` methods against an `AuditContext` (SSH, DB, limits, clock). Avoid cross-coupling; add new checks by adding new plug-ins.
2. **Resumable Execution:** sessions and per-check status stored in DB (`sessions`, `check_runs`, `errors`). Never lose progress; write rows atomically.
3. **Data Model:** normalized tables for packages, verification results, users/groups, history, logins, sockets, processes/open files, services, nmap, resources, disks, OS, firewall, netif, hardware. Content snapshots are gzip-compressed, size-capped, and de-duplicated by SHA-256 (`file_snapshots`).
4. **Security & Privacy:** read-only posture; sudo limited to specific commands; strict size caps and allow-list for text/config snapshots; timestamps normalized to UTC.
5. **Non-goals:** v1 is serial (no concurrency), CentOS 7.6 first, no agent install on targets.

## Toolbox & Conventions
- **SSH:** Paramiko preferred; fallback to system `ssh` via subprocess. Provide `sudo` escalation and `which()` probing. Timeouts per command.
- **Parsing:** Favor robust formats and filters (`--qf` for rpm, JSON where available, `-oX` for nmap). Include tests.
- **Progress UX:** Use `tqdm` or `rich` if available; otherwise plain text.
- **Database:** SQLite, schema in `docs/schema.sql`. Use foreign keys and transactions. Keep blobs compressed and deduped.
- **OS Target:** CentOS 7.6 / RHEL 7 lineage; prefer tools available on that platform (`ss`, `rpm`, `yum`, `systemctl`, `last`, `lsof`, etc.).

## Typical Tasks for You (Agent)
- Implement new Strategy plug-ins (e.g., `services.py`, `firewall.py`, `nmap_scan.py`) adhering to the base interface.
- Write parsers for command outputs with unit tests.
- Extend the schema safely with migrations.
- Improve resume logic, logging, or progress UX without breaking Strategy contracts.
- Add reporting/exporters (future).
- Keep everything portable for USB usage.

## Quick Context Links
- Requirements: `docs/requirements.md`
- Architecture: `docs/architecture.md`
- Check specifications: `docs/check-specs.md`
- Data model & ERD: `docs/data-model.md`
- Schema: `docs/schema.sql`
- Security: `docs/security.md`
- Ops Playbook: `docs/ops-playbook.md`
- Test plan: `docs/test-plan.md`

When responding, cite which components you are modifying (files/classes/functions) and provide diffs or file drops as appropriate.
