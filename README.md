# Auditron — Portable Host Auditing Suite (CentOS 7.6)

**Version:** 0.1.0 • **Last updated:** 2025-09-16 22:06:45Z

Auditron is a USB-hosted, agentless auditing tool for CentOS 7.6 fleets. It SSHes into configured hosts, runs a modular set of checks (Strategy pattern), and stores configuration + results in a SQLite DB on the USB drive. Sessions are resumable; every check is toggleable globally and per-host.

## Repo Layout

```
auditron/
├── auditron.py               # CLI entrypoint (orchestrator)
├── strategies/              # Modular Strategy plug-ins (checks)
│   ├── base.py
│   ├── rpm_inventory.py
│   ├── rpm_verify.py
│   ├── sockets.py
│   ├── processes.py
│   └── osinfo.py
├── utils/                   # Helpers (SSH, DB, parsing, compression)
│   ├── ssh_runner.py
│   ├── db.py
│   ├── parsing.py
│   └── compress.py
├── scripts/
│   └── seed_db.py          # Initialize global defaults + add sample hosts
├── docs/                   # All documentation
│   ├── overview.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── check-specs.md
│   ├── data-model.md
│   ├── schema.sql
│   ├── security.md
│   ├── ops-playbook.md
│   ├── test-plan.md
│   ├── future.md
│   └── cli-bootstrap.md
├── seed-prompt.md          # Context bootstrap prompt for agents
├── db/                     # SQLite DB directory (created at runtime)
└── logs/                   # Run logs
```

## Documentation Index

- [docs/overview.md](docs/overview.md) — Vision, scope, goals, and non-goals
- [docs/requirements.md](docs/requirements.md) — Functional & non-functional requirements
- [docs/architecture.md](docs/architecture.md) — Strategy architecture, components, exec & resume flow, progress UX
- [docs/check-specs.md](docs/check-specs.md) — Command-level specifications for every audit check
- [docs/data-model.md](docs/data-model.md) — ERD (Mermaid) and normalization approach
- [docs/schema.sql](docs/schema.sql) — SQLite schema (initial cut)
- [docs/security.md](docs/security.md) — Security & privacy posture, data handling
- [docs/ops-playbook.md](docs/ops-playbook.md) — Operational guidance and USB setup
- [docs/test-plan.md](docs/test-plan.md) — v1 test plan (unit, integration, resume)
- [docs/future.md](docs/future.md) — Roadmap (concurrency, reporting, exporters)
- [docs/cli-bootstrap.md](docs/cli-bootstrap.md) — CLI usage examples and bootstrap notes

## Quick Start

```bash
# 1) Create a venv (optional) and install deps (paramiko recommended)
python3 -m venv .venv && source .venv/bin/activate
pip install paramiko tqdm rich

# 2) Initialize the DB and defaults
sqlite3 db/auditron.db < docs/schema.sql
python scripts/seed_db.py --init-defaults
python scripts/seed_db.py --add-host host1 --ip 192.168.1.10 --user centos --key ~/.ssh/id_rsa

# 3) Run Auditron (interactive resume/new)
python auditron.py
```

## Seed Prompt

See [seed-prompt.md](seed-prompt.md) for a context-rich bootstrap message you can paste into ChatGPT/agents when working on Auditron.
