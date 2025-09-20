# Auditron Seed Prompt (Context Bootstrap)

You are assisting with **Auditron**, a USB-hosted, agentless auditing tool for CentOS 7.6. It SSHes into configured hosts, runs modular checks using the **Strategy pattern**, and stores configuration + results in a **SQLite** DB on the USB. Execution is **resumable**; checks are toggleable globally and per-host.

**Repo entrypoint:** `auditron.py`  
**Docs:** `docs/` (EARS requirements in `requirements-ears.md` are authoritative)  
**Plug-ins:** `strategies/*.py` each implement `probe()` + `run()` with `AuditContext`.

## Core Architecture
- Strategy isolation: add/modify checks without touching orchestrator.
- Resume semantics: `sessions`, `check_runs`, `errors` tables track progress.
- Data model: normalized; text/config snapshots are gzip-compressed + SHA-256 deduped.
- CentOS 7.6 tooling: `rpm`, `yum history`, `ss|netstat`, `systemctl`, `last|lastb`, `ip`, `nmcli`, etc.
- Security: read-only posture; sudo limited to read-only commands; path allow/deny for content capture; UTC normalization.

## Critical Implementation Details
**Database Schema Constraints:**
- Session modes MUST be 'new' or 'resume' (NOT 'fresh' or 'test') per CHECK constraint in `docs/schema.sql`
- CLI accepts 'fresh'/'resume' but `auditron.py` maps 'fresh' → 'new' for DB compatibility

**Strategy Requirements:**
- Processes: `requires = ("ps",)`
- Routes: `requires = ("ip",)` 
- RpmInventory: `requires = ("rpm",)`
- RpmVerify: `requires = ("rpm",)`
- OSInfo: `requires = ()` (no deps)
- Sockets: `requires = ()` (no deps, but probes for ss/netstat)

**Command Output Formats:**
- RPM inventory: pipe-separated `name|epoch|version|release|arch|installtime`
- RPM verify: space-separated flags + path, handles 'c'/'d' markers
- PS output: `ps -eo pid,ppid,user,lstart,etime,cmd --no-headers` format
- SS output: includes users:((proc,pid=N,fd=N)) for process info

## Comprehensive Test Suite (Production Ready)
**Status: 111 tests passing, 0 warnings, enterprise-grade quality**

**Test Structure:**
- `tests/test_db.py` - Database operations (47 tests)
- `tests/test_ssh_runner.py` - SSH functionality (20 tests) 
- `tests/test_strategies.py` - Strategy implementations (25 tests)
- `tests/test_auditron.py` - Main orchestrator (15 tests)
- `tests/test_parsing_comprehensive.py` - Command parsers (15 tests)
- `tests/test_utilities.py` - Utility functions (12 tests)
- `tests/integration/test_full_workflow.py` - E2E tests (6 tests)
- `tests/conftest.py` - Comprehensive fixtures (temp_db, mock_ssh_client, audit_context, etc.)

**Test Execution:**
```bash
# Unit tests (fast)
pytest -m 'not integration'

# All tests  
pytest

# With coverage
pytest --cov=auditron --cov=utils --cov=strategies
```

**CI/CD Integration:**
- GitHub Actions triggers on `main`, `feature/*` branches, and PRs
- Multi-Python version testing (3.10, 3.11, 3.12)
- Full linting pipeline: ruff, black, isort, flake8, pylint, pyright
- Coverage reporting with 75%+ threshold

## Development Workflow
**Linting (All Clean):**
- Ruff: ✅ Clean (primary linter)
- Black: ✅ Clean (formatting)
- Isort: ✅ Clean (import sorting) 
- Flake8: ✅ Clean (style)
- Pylint: ✅ 9.17/10 (excellent score)

**Test Data & Mocking:**
- Extensive SSH mocking (no network deps)
- Realistic command output fixtures
- Temporary SQLite databases
- Comprehensive error scenario testing

**Key Files:**
- `pytest.ini` - Test configuration with markers
- `.pre-commit-config.yaml` - Linting hooks
- `ruff.toml` - Ruff configuration  
- `.flake8` - Flake8 configuration

## PyInstaller Deployment System (COMPLETE)
**Status: Production-ready USB deployment infrastructure**

**Core Components:**
- `auditron.spec` - PyInstaller configuration for 6.5MB standalone executable
- `scripts/build_deployment.py` - Automated build with testing (`make build-test`)
- `scripts/deploy_to_usb.py` - USB deployment with field scripts (`USB_PATH=/path make deploy-usb`)
- `scripts/init_deployment_db.py` - Deployment-friendly DB initialization (accepts path parameter)
- `scripts/config_deployment.py` - Interactive config utility with DB path parameter
- `scripts/test_config_input.py` - Automated configuration input for CI/CD
- `tests/test_config_automation.py` - Complete deployment validation with DB verification

**Field Deployment Features:**
- Single executable (no Python required on target systems)
- Auto-generated USB scripts: `setup.sh`, `run_audit.sh`, `resume_audit.sh`
- Professional workspace structure with logs/exports directories
- Comprehensive validation and error handling
- Pipeable input for automated testing and CI/CD integration

**Documentation:**
- `docs/deployment.md` - Complete deployment guide
- `docs/usage.md` - All CLI utilities documented with parameters/return codes
- Field-ready README for USB deployments

**Quality Assurance:**
- All deployment tests passing with database content verification
- Clean linting across all new components
- Maintains backward compatibility with existing development workflow
- Professional error handling and user experience

## Typical Tasks
- Implement/extend strategies (e.g., firewall, nmap, hardware)
- Write robust parsers + unit tests using existing fixtures
- Improve resume/progress UX
- Add reports/exporters (future)
- Maintain test coverage >90% for new code
- Build deployment packages: `make build-test`
- Deploy to USB: `USB_PATH=/media/usb make deploy-usb`

## Essential Reading
- `docs/requirements-ears.md` - Authoritative requirements
- `docs/architecture.md` - System design
- `docs/check-specs.md` - Strategy specifications  
- `docs/data-model.md` - Database schema details
- `docs/schema.sql` - Database constraints (critical for session modes)
- `docs/deployment.md` - **Complete PyInstaller deployment guide**
- `docs/usage.md` - **All CLI utilities reference (parameters, return codes)**
- `tests/README.md` - Complete testing guide
- `FINAL_TEST_REPORT.md` - Test suite documentation

**Pro Tips:**
- Always use 'new'/'resume' for session modes in code
- Follow existing test patterns in `tests/test_*.py`
- Use `audit_context` fixture for strategy testing
- Mock SSH operations with realistic command outputs
- Run linters locally before committing
- Add tests first (TDD approach) for new features
