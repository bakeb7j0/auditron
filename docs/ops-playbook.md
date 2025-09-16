# Operational Playbook

## USB Preparation
- Partition and format the USB (optionally encrypt with LUKS).
- Copy the Auditron repo onto the USB. Optionally bundle a Python 3.11 venv.

## Database Initialization
- Execute `docs/schema.sql` against `auditron.db` (SQLite) on the USB.
- Insert a row into `global_defaults` (ID = 1) enabling all checks.
- Add hosts to `hosts` with SSH details and `use_sudo` as appropriate.

## Running
- Start `auditron.py`.
- Choose **resume** if a previous session is incomplete; otherwise **new**.
- Watch console progress (overall + per‑check).

## After Run
- Export tables (CSV) for reporting or ingest the DB into analytics.
