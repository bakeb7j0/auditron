VENV=.venv
PY=python3
DEPLOYMENT_DIR=deployment
USB_DIR=auditron

# Default target
all: install

# Development environment setup
venv:
	$(PY) -m venv $(VENV)

install: venv
	. $(VENV)/bin/activate && pip install -r requirements-dev.txt

# PyInstaller deployment dependencies
install-deploy:
	@echo "Checking PyInstaller installation..."
	@pyinstaller --version >/dev/null 2>&1 || { echo "Installing PyInstaller..."; pip install --user pyinstaller; }
	@echo "PyInstaller ready"

# Database operations
db:
	sqlite3 db/auditron.db < docs/schema.sql

seed:
	. $(VENV)/bin/activate && python scripts/seed_db.py --init-defaults

# Development execution
run:
	. $(VENV)/bin/activate && python auditron.py

config:
	. $(VENV)/bin/activate && python scripts/config_utility.py

# Testing
test:
	. $(VENV)/bin/activate && pytest -q

test-all:
	. $(VENV)/bin/activate && pytest --cov=auditron --cov=utils --cov=strategies

# Linting
lint:
	. $(VENV)/bin/activate && ruff check .
	. $(VENV)/bin/activate && black --check .
	. $(VENV)/bin/activate && isort --check-only .

format:
	. $(VENV)/bin/activate && black .
	. $(VENV)/bin/activate && isort .

# Deployment targets
build: install-deploy
	python3 scripts/build_deployment.py --clean

build-test: install-deploy
	python3 scripts/build_deployment.py --clean --test

package: build
	@echo "📦 Deployment package ready in $(DEPLOYMENT_DIR)/"
	@ls -la $(DEPLOYMENT_DIR)/

# USB deployment (requires USB_PATH environment variable)
deploy-usb: package
	@if [ -z "$$USB_PATH" ]; then \
		echo "❌ Set USB_PATH environment variable (e.g., USB_PATH=/media/user/AUDITRON make deploy-usb)"; \
		exit 1; \
	fi
	python3 scripts/deploy_to_usb.py "$$USB_PATH" --deployment-dir $(DEPLOYMENT_DIR)

# Clean targets
clean:
	rm -rf build/ dist/ *.spec

clean-deployment:
	rm -rf $(DEPLOYMENT_DIR)/

clean-all: clean clean-deployment
	rm -rf $(VENV)/ .pytest_cache/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Development helpers
dev-setup: install
	. $(VENV)/bin/activate && pre-commit install

check: lint test

# Metrics management
update-metrics:
	python3 scripts/update_metrics.py --verbose

check-metrics:
	python3 scripts/update_metrics.py --check-only

enforce-quality:
	python3 scripts/update_metrics.py --enforce-quality --verbose

# Show available targets
help:
	@echo "Available targets:"
	@echo "  install       - Install development dependencies"
	@echo "  install-deploy- Install deployment dependencies"
	@echo "  test          - Run tests (quick)"
	@echo "  test-all      - Run tests with coverage"
	@echo "  lint          - Run all linters"
	@echo "  format        - Auto-format code"
	@echo "  build         - Build deployment package"
	@echo "  build-test    - Build and test deployment package"
	@echo "  package       - Show deployment package contents"
	@echo "  deploy-usb    - Deploy to USB (set USB_PATH=/path/to/usb)"
	@echo "  clean         - Clean build artifacts"
	@echo "  clean-all     - Clean everything including venv"
	@echo "  dev-setup     - Setup development environment with pre-commit"
	@echo "  check         - Run lint + test"

.PHONY: all venv install install-deploy db seed run config test test-all lint format \
        build build-test package deploy-usb clean clean-deployment clean-all \
        dev-setup check help
