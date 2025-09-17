# Auditron — Portable Host Auditing Suite (CentOS 7.6)

Auditron is a USB-hosted, agentless auditing tool for CentOS 7.6 fleets. It SSHes into configured hosts, runs modular checks (Strategy pattern), and stores configuration + results in a SQLite DB on the USB. Sessions are resumable; every check is toggleable globally and per-host.

## Repo Layout
```
auditron/
├── auditron.py               # CLI orchestrator (serial v1)
├── strategies/              # Strategy plug-ins (checks)
│   ├── base.py
│   ├── rpm_inventory.py
│   ├── rpm_verify.py
│   ├── sockets.py
│   ├── processes.py
│   ├── osinfo.py
│   └── routes.py            # NEW: current + configured routing tables
├── utils/
│   ├── ssh_runner.py
│   ├── db.py
│   ├── parsing.py
│   └── compress.py
├── scripts/
│   ├── seed_db.py           # init defaults + add hosts
│   └── config_utility.py    # menu-based console config editor
├── docs/
│   ├── overview.md
│   ├── requirements-ears.md # EARS-form requirements (authoritative)
│   ├── architecture.md
│   ├── check-specs.md
│   ├── data-model.md
│   ├── schema.sql
│   ├── security.md
│   ├── ops-playbook.md
│   ├── test-plan.md
│   ├── future.md
│   └── cli-bootstrap.md
├── seed-prompt.md
├── Makefile
└── tests/
    └── test_parsers.py
```

## Quick Start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install paramiko tqdm rich pytest

sqlite3 db/auditron.db < docs/schema.sql
python scripts/seed_db.py --init-defaults
python scripts/seed_db.py --add-host host1 --ip 192.168.1.10 --user centos --key ~/.ssh/id_rsa --sudo

python auditron.py
# open TUI config:
python scripts/config_utility.py
```

## Docs Index
- [docs/requirements-ears.md](docs/requirements-ears.md) — **EARS** requirements
- [docs/architecture.md](docs/architecture.md) — Strategy architecture, flow, resume, progress
- [docs/check-specs.md](docs/check-specs.md) — Command-level specs (CentOS 7.6)
- [docs/data-model.md](docs/data-model.md) — ERD + normalization
- [docs/schema.sql](docs/schema.sql) — SQLite schema
- [docs/security.md](docs/security.md) — Security & privacy
- [docs/ops-playbook.md](docs/ops-playbook.md) — USB setup, run book
- [docs/test-plan.md](docs/test-plan.md) — v1 tests
- [docs/future.md](docs/future.md) — roadmap
- [docs/cli-bootstrap.md](docs/cli-bootstrap.md) — CLI examples
