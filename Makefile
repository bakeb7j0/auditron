VENV=.venv
PY=python3
all: install
venv:
	$(PY) -m venv $(VENV)
install: venv
	. $(VENV)/bin/activate && pip install -U pip paramiko tqdm rich pytest
db:
	sqlite3 db/auditron.db < docs/schema.sql
seed:
	. $(VENV)/bin/activate && python scripts/seed_db.py --init-defaults
run:
	. $(VENV)/bin/activate && python auditron.py
config:
	. $(VENV)/bin/activate && python scripts/config_utility.py
test:
	. $(VENV)/bin/activate && pytest -q
