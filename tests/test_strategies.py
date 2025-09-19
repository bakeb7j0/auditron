"""Unit tests for strategy implementations."""

from unittest.mock import Mock

import pytest

from strategies.base import AuditCheck, AuditContext
from strategies.osinfo import OSInfo
from strategies.processes import Processes
from strategies.routes import Routes
from strategies.rpm_inventory import RpmInventory
from strategies.rpm_verify import RpmVerify
from strategies.sockets import Sockets
from utils.ssh_runner import SSHResult


class TestAuditContext:
    """Test AuditContext class."""

    def test_audit_context_init(
        self, sample_host, mock_ssh_client, temp_db, mock_clock
    ):
        """Test AuditContext initialization."""
        ctx = AuditContext(
            host=sample_host,
            ssh=mock_ssh_client,
            db=temp_db,
            limits={},
            clock=mock_clock,
            session_id=1,
        )

        assert ctx.host == sample_host
        assert ctx.ssh == mock_ssh_client
        assert ctx.db == temp_db
        assert ctx.limits == {}
        assert ctx.clock == mock_clock
        assert ctx.session_id == 1


class TestAuditCheckBase:
    """Test AuditCheck base class."""

    def test_audit_check_abstract(self):
        """Test that AuditCheck is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="abstract"):
            AuditCheck()  # pylint: disable=abstract-class-instantiated  # type: ignore[abstract]

    def test_audit_check_default_probe(self):
        """Test default probe implementation."""

        class TestCheck(AuditCheck):
            name = "test"

            def run(self, ctx):
                pass

        check = TestCheck()
        ctx = Mock()
        assert check.probe(ctx) is True  # Default implementation returns True


class TestOSInfoStrategy:
    """Test OSInfo strategy."""

    def test_osinfo_basic_attributes(self):
        """Test OSInfo basic attributes."""
        strategy = OSInfo()
        assert strategy.name == "osinfo"
        assert strategy.requires == ()

    def test_osinfo_probe_always_true(self, audit_context):
        """Test that OSInfo probe always returns True."""
        strategy = OSInfo()
        assert strategy.probe(audit_context) is True

    def test_osinfo_run_success(self, audit_context, os_release_output, uname_output):
        """Test successful OSInfo execution."""
        # Mock SSH responses
        audit_context.ssh.run.side_effect = [
            SSHResult(0, os_release_output, ""),  # os-release command
            SSHResult(0, uname_output, ""),  # uname command
        ]

        strategy = OSInfo()
        strategy.run(audit_context)

        # Verify data was inserted into database
        os_info = audit_context.db.execute(
            "SELECT name, version_id, kernel FROM os_info WHERE host_id = ?",
            (audit_context.host["id"],),
        ).fetchone()

        assert os_info is not None
        assert os_info[0] == "CentOS Linux"
        assert os_info[1] == "7"
        assert "Linux" in os_info[2]

    def test_osinfo_run_command_failure(self, audit_context):
        """Test OSInfo handling of command failure."""
        # Mock SSH failure
        audit_context.ssh.run.side_effect = [
            SSHResult(1, "", "Permission denied"),  # os-release command fails
            SSHResult(0, "Linux", ""),  # uname command succeeds
        ]

        strategy = OSInfo()
        strategy.run(audit_context)

        # Verify error was recorded
        error = audit_context.db.execute(
            "SELECT stderr, exit_code FROM errors WHERE check_run_id IN "
            "(SELECT id FROM check_runs WHERE check_name = 'osinfo')"
        ).fetchone()

        assert error is not None
        assert "Permission denied" in error[0]
        assert error[1] == 1

    def test_osinfo_run_exception_handling(self, audit_context):
        """Test OSInfo handling of exceptions."""
        # Mock SSH to raise an exception
        audit_context.ssh.run.side_effect = Exception("Network error")

        strategy = OSInfo()
        strategy.run(audit_context)

        # Verify error was recorded
        check_run = audit_context.db.execute(
            "SELECT status, reason FROM check_runs WHERE check_name = 'osinfo'"
        ).fetchone()

        assert check_run[0] == "ERROR"
        assert "Network error" in check_run[1]


class TestSocketsStrategy:
    """Test Sockets strategy."""

    def test_sockets_basic_attributes(self):
        """Test Sockets basic attributes."""
        strategy = Sockets()
        assert strategy.name == "sockets"
        assert strategy.requires == ()

    def test_sockets_probe_checks_ss_availability(self, audit_context):
        """Test that Sockets probe checks for ss command availability."""
        audit_context.ssh.which.return_value = True

        strategy = Sockets()
        assert strategy.probe(audit_context) is True

        audit_context.ssh.which.assert_called_with("ss")

    def test_sockets_probe_fallback_to_netstat(self, audit_context):
        """Test that Sockets probe falls back to netstat when ss unavailable."""
        audit_context.ssh.which.side_effect = lambda cmd: cmd == "netstat"

        strategy = Sockets()
        assert strategy.probe(audit_context) is True

    def test_sockets_probe_fails_when_no_tools(self, audit_context):
        """Test that Sockets probe fails when neither ss nor netstat available."""
        audit_context.ssh.which.return_value = False

        strategy = Sockets()
        assert strategy.probe(audit_context) is False

    def test_sockets_run_with_ss(self, audit_context, ss_listen_output):
        """Test Sockets execution using ss command."""
        audit_context.ssh.which.return_value = True
        audit_context.ssh.run.return_value = SSHResult(0, ss_listen_output, "")

        strategy = Sockets()
        strategy.run(audit_context)

        # Verify sockets were parsed and stored
        sockets = audit_context.db.execute(
            "SELECT proto, local, state, pid, process FROM listen_sockets WHERE host_id = ?",
            (audit_context.host["id"],),
        ).fetchall()

        assert len(sockets) >= 3  # Should have parsed multiple sockets

        # Check for SSH socket
        ssh_sockets = [s for s in sockets if s[4] == "sshd"]
        assert len(ssh_sockets) >= 1
        assert ssh_sockets[0][0] == "tcp"


class TestProcessesStrategy:
    """Test Processes strategy."""

    def test_processes_basic_attributes(self):
        """Test Processes basic attributes."""
        strategy = Processes()
        assert strategy.name == "processes"
        assert strategy.requires == ("ps",)

    def test_processes_probe_checks_ps_availability(self, audit_context):
        """Test that Processes probe checks for ps command availability."""
        audit_context.ssh.which.return_value = True

        strategy = Processes()
        assert strategy.probe(audit_context) is True

        audit_context.ssh.which.assert_called_with("ps")

    def test_processes_run_success(self, audit_context, ps_output):
        """Test successful Processes execution."""
        audit_context.ssh.which.return_value = True
        audit_context.ssh.run.return_value = SSHResult(0, ps_output, "")

        strategy = Processes()
        strategy.run(audit_context)

        # Verify processes were parsed and stored
        processes = audit_context.db.execute(
            "SELECT pid, ppid, user, cmd FROM processes WHERE host_id = ?",
            (audit_context.host["id"],),
        ).fetchall()

        assert len(processes) >= 3  # Should have parsed multiple processes

        # Check for init process
        init_process = next((p for p in processes if p[0] == 1), None)
        assert init_process is not None
        assert init_process[1] == 0  # ppid should be 0
        assert init_process[2] == "root"


class TestRoutesStrategy:
    """Test Routes strategy."""

    def test_routes_basic_attributes(self):
        """Test Routes basic attributes."""
        strategy = Routes()
        assert strategy.name == "routes"
        assert strategy.requires == ("ip",)

    def test_routes_probe_checks_ip_availability(self, audit_context):
        """Test that Routes probe checks for ip command availability."""
        audit_context.ssh.which.return_value = True

        strategy = Routes()
        assert strategy.probe(audit_context) is True

        audit_context.ssh.which.assert_called_with("ip")

    def test_routes_run_success(self, audit_context, ip_route_output):
        """Test successful Routes execution."""
        audit_context.ssh.which.return_value = True
        audit_context.ssh.run.return_value = SSHResult(0, ip_route_output, "")

        strategy = Routes()
        strategy.run(audit_context)

        # Verify route data was stored
        routes = audit_context.db.execute(
            "SELECT content FROM routing_state WHERE host_id = ? AND kind = 'current'",
            (audit_context.host["id"],),
        ).fetchone()

        assert routes is not None
        assert "default via" in routes[0]
        assert "192.168.1.0/24" in routes[0]


class TestRpmInventoryStrategy:
    """Test RPM Inventory strategy."""

    def test_rpm_inventory_basic_attributes(self):
        """Test RpmInventory basic attributes."""
        strategy = RpmInventory()
        assert strategy.name == "rpm_inventory"
        assert strategy.requires == ("rpm",)

    def test_rpm_inventory_probe_checks_rpm_availability(self, audit_context):
        """Test that RpmInventory probe checks for rpm command availability."""
        audit_context.ssh.which.return_value = True

        strategy = RpmInventory()
        assert strategy.probe(audit_context) is True

        audit_context.ssh.which.assert_called_with("rpm")

    def test_rpm_inventory_run_success(self, audit_context):
        """Test successful RpmInventory execution."""
        rpm_output = """bash|(none)|4.2.46|34.el7|x86_64|1234567890
kernel|(none)|3.10.0|1160.el7|x86_64|1234567891
openssh|(none)|7.4p1|22.el7_9|x86_64|1234567892"""

        audit_context.ssh.which.return_value = True
        audit_context.ssh.run.return_value = SSHResult(0, rpm_output, "")

        strategy = RpmInventory()
        strategy.run(audit_context)

        # Verify packages were parsed and stored
        packages = audit_context.db.execute(
            "SELECT name, version, release, arch FROM rpm_packages WHERE host_id = ?",
            (audit_context.host["id"],),
        ).fetchall()

        assert len(packages) >= 3

        # Check for bash package
        bash_package = next((p for p in packages if p[0] == "bash"), None)
        assert bash_package is not None
        assert bash_package[1] == "4.2.46"
        assert bash_package[2] == "34.el7"
        assert bash_package[3] == "x86_64"


class TestRpmVerifyStrategy:
    """Test RPM Verify strategy."""

    def test_rpm_verify_basic_attributes(self):
        """Test RpmVerify basic attributes."""
        strategy = RpmVerify()
        assert strategy.name == "rpm_verify"
        assert strategy.requires == ("rpm",)

    def test_rpm_verify_probe_checks_rpm_availability(self, audit_context):
        """Test that RpmVerify probe checks for rpm command availability."""
        audit_context.ssh.which.return_value = True

        strategy = RpmVerify()
        assert strategy.probe(audit_context) is True

        audit_context.ssh.which.assert_called_with("rpm")

    def test_rpm_verify_run_success(self, audit_context, rpm_verify_output):
        """Test successful RpmVerify execution."""
        audit_context.ssh.which.return_value = True
        audit_context.ssh.run.return_value = SSHResult(0, rpm_verify_output, "")

        strategy = RpmVerify()
        strategy.run(audit_context)

        # Verify verified files were parsed and stored
        verified_files = audit_context.db.execute(
            "SELECT path, verify_flags, changed FROM rpm_verified_files WHERE host_id = ?",
            (audit_context.host["id"],),
        ).fetchall()

        assert len(verified_files) >= 4

        # Check for modified files
        modified_files = [f for f in verified_files if f[2] == 1]  # changed = 1
        assert len(modified_files) >= 2  # Should have some modified files


class TestStrategyIntegration:
    """Integration tests for strategy execution."""

    def test_all_strategies_can_be_instantiated(self):
        """Test that all strategies can be instantiated."""
        strategies = [OSInfo, Processes, Routes, RpmInventory, RpmVerify, Sockets]

        for strategy_class in strategies:
            strategy = strategy_class()
            assert hasattr(strategy, "name")
            assert hasattr(strategy, "requires")
            assert hasattr(strategy, "probe")
            assert hasattr(strategy, "run")

    def test_strategy_names_are_unique(self):
        """Test that all strategy names are unique."""
        strategies = [
            OSInfo(),
            Processes(),
            Routes(),
            RpmInventory(),
            RpmVerify(),
            Sockets(),
        ]
        names = [s.name for s in strategies]

        assert len(names) == len(set(names)), "Strategy names must be unique"

    def test_strategies_have_valid_requires(self):
        """Test that all strategies have valid requires tuples."""
        strategies = [
            OSInfo(),
            Processes(),
            Routes(),
            RpmInventory(),
            RpmVerify(),
            Sockets(),
        ]

        for strategy in strategies:
            assert isinstance(strategy.requires, tuple)
            # All requires should be strings
            assert all(isinstance(req, str) for req in strategy.requires)
