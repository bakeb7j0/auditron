"""Unit tests for main Auditron orchestrator."""

from unittest.mock import Mock, patch

import pytest

import auditron


class TestCliParsing:
    """Test command-line interface parsing."""

    def test_parse_cli_fresh_positional(self):
        """Test parsing fresh mode as positional argument."""
        with patch("sys.argv", ["auditron.py", "fresh"]):
            mode, db_path = auditron.parse_cli()
            assert mode == "fresh"
            assert db_path == "auditron.db"  # default

    def test_parse_cli_resume_positional(self):
        """Test parsing resume mode as positional argument."""
        with patch("sys.argv", ["auditron.py", "resume"]):
            mode, db_path = auditron.parse_cli()
            assert mode == "resume"
            assert db_path == "auditron.db"

    def test_parse_cli_fresh_flag(self):
        """Test parsing fresh mode as flag."""
        with patch("sys.argv", ["auditron.py", "--fresh"]):
            mode, db_path = auditron.parse_cli()
            assert mode == "fresh"

    def test_parse_cli_resume_flag(self):
        """Test parsing resume mode as flag."""
        with patch("sys.argv", ["auditron.py", "--resume"]):
            mode, db_path = auditron.parse_cli()
            assert mode == "resume"

    def test_parse_cli_custom_db_path(self):
        """Test parsing with custom database path."""
        with patch("sys.argv", ["auditron.py", "--db", "/tmp/test.db", "--fresh"]):
            mode, db_path = auditron.parse_cli()
            assert mode == "fresh"
            assert db_path == "/tmp/test.db"

    def test_parse_cli_conflicting_modes_error(self):
        """Test that conflicting modes raise an error."""
        with patch("sys.argv", ["auditron.py", "fresh", "--resume"]):
            with pytest.raises(SystemExit):
                auditron.parse_cli()

    def test_parse_cli_no_mode_error(self):
        """Test that missing mode raises an error."""
        with patch("sys.argv", ["auditron.py"]):
            with pytest.raises(SystemExit):
                auditron.parse_cli()

    def test_parse_cli_invalid_mode_error(self):
        """Test that invalid mode raises an error."""
        with patch("sys.argv", ["auditron.py", "invalid"]):
            with pytest.raises(SystemExit):
                auditron.parse_cli()


class TestRunAllChecks:
    """Test run_all_checks function."""

    @patch("auditron.OSInfo")
    @patch("auditron.Processes")
    @patch("auditron.Routes")
    @patch("auditron.RpmInventory")
    @patch("auditron.RpmVerify")
    @patch("auditron.Sockets")
    def test_run_all_checks_executes_all_strategies(
        self,
        mock_sockets,
        mock_rpm_verify,
        mock_rpm_inventory,
        mock_routes,
        mock_processes,
        mock_osinfo,
        audit_context,
    ):
        """Test that run_all_checks executes all strategy classes."""
        # Mock strategy instances
        for mock_strategy_class in [
            mock_osinfo,
            mock_processes,
            mock_routes,
            mock_rpm_inventory,
            mock_rpm_verify,
            mock_sockets,
        ]:
            mock_instance = Mock()
            mock_strategy_class.return_value = mock_instance

        auditron.run_all_checks(audit_context)

        # Verify all strategies were instantiated and run
        for mock_strategy_class in [
            mock_osinfo,
            mock_processes,
            mock_routes,
            mock_rpm_inventory,
            mock_rpm_verify,
            mock_sockets,
        ]:
            mock_strategy_class.assert_called_once()
            mock_strategy_class.return_value.run.assert_called_once_with(audit_context)

    def test_run_all_checks_with_real_strategies(self, audit_context):
        """Test run_all_checks with real strategy classes (integration-style)."""
        # Mock SSH responses for all strategies
        audit_context.ssh.which.return_value = True
        audit_context.ssh.run.return_value = Mock(rc=0, out="mock output", err="")

        # Should not raise any exceptions
        auditron.run_all_checks(audit_context)

        # Verify some check runs were created
        check_runs = audit_context.db.execute(
            "SELECT check_name FROM check_runs WHERE host_id = ?",
            (audit_context.host["id"],),
        ).fetchall()

        expected_checks = {
            "osinfo",
            "processes",
            "routes",
            "rpm_inventory",
            "rpm_verify",
            "sockets",
        }
        actual_checks = {row[0] for row in check_runs}

        assert expected_checks.issubset(actual_checks)


class TestRunMode:
    """Test run_mode function."""

    @patch("auditron.run_all_checks")
    @patch("auditron.SSHClient")
    @patch("auditron.db")
    def test_run_mode_fresh(
        self, mock_db, mock_ssh_client_class, mock_run_all_checks, temp_db
    ):
        """Test run_mode with fresh mode."""
        # Setup mocks
        mock_db.connect.return_value = temp_db
        mock_db.ensure_schema.return_value = None
        mock_db.new_session.return_value = 1
        mock_db.get_hosts.return_value = [
            {"id": 1, "hostname": "test-host", "ip": "192.168.1.100"}
        ]
        mock_db.finish_session.return_value = None

        mock_ssh_instance = Mock()
        mock_ssh_client_class.return_value = mock_ssh_instance

        auditron.run_mode("test.db", "new")

        # Verify database operations
        mock_db.connect.assert_called_once_with("test.db")
        mock_db.ensure_schema.assert_called_once_with(temp_db)
        mock_db.new_session.assert_called_once_with(temp_db, "new")
        mock_db.get_hosts.assert_called_once_with(temp_db)
        mock_db.finish_session.assert_called_once_with(temp_db, 1)

        # Verify SSH client was created and checks were run
        mock_ssh_client_class.assert_called_once()
        mock_run_all_checks.assert_called_once()

    @patch("auditron.run_all_checks")
    @patch("auditron.SSHClient")
    @patch("auditron.db")
    def test_run_mode_multiple_hosts(
        self, mock_db, mock_ssh_client_class, mock_run_all_checks, temp_db
    ):
        """Test run_mode with multiple hosts."""
        # Setup mocks with multiple hosts
        mock_db.connect.return_value = temp_db
        mock_db.ensure_schema.return_value = None
        mock_db.new_session.return_value = 1
        mock_db.get_hosts.return_value = [
            {"id": 1, "hostname": "host1", "ip": "192.168.1.10"},
            {"id": 2, "hostname": "host2", "ip": "192.168.1.20"},
            {"id": 3, "hostname": "host3", "ip": "192.168.1.30"},
        ]
        mock_db.finish_session.return_value = None

        auditron.run_mode("test.db", "new")

        # Verify SSH client was created for each host
        assert mock_ssh_client_class.call_count == 3
        assert mock_run_all_checks.call_count == 3

    @patch("auditron.run_all_checks")
    @patch("auditron.SSHClient")
    @patch("auditron.db")
    def test_run_mode_no_hosts(
        self, mock_db, mock_ssh_client_class, mock_run_all_checks, temp_db
    ):
        """Test run_mode with no configured hosts."""
        # Setup mocks with no hosts
        mock_db.connect.return_value = temp_db
        mock_db.ensure_schema.return_value = None
        mock_db.new_session.return_value = 1
        mock_db.get_hosts.return_value = []
        mock_db.finish_session.return_value = None

        auditron.run_mode("test.db", "new")

        # Verify session was still created and finished
        mock_db.new_session.assert_called_once()
        mock_db.finish_session.assert_called_once()

        # But no SSH clients or checks should have been created
        mock_ssh_client_class.assert_not_called()
        mock_run_all_checks.assert_not_called()


class TestRunResume:
    """Test run_resume function."""

    @patch("auditron.run_all_checks")
    @patch("auditron.SSHClient")
    @patch("auditron.db")
    def test_run_resume_with_unfinished_session(
        self, mock_db, mock_ssh_client_class, mock_run_all_checks, temp_db
    ):
        """Test run_resume when there's an unfinished session."""
        # Setup mocks
        mock_db.connect.return_value = temp_db
        mock_db.ensure_schema.return_value = None
        mock_db.get_unfinished_session.return_value = 2
        mock_db.get_hosts.return_value = [
            {"id": 1, "hostname": "test-host", "ip": "192.168.1.100"}
        ]
        mock_db.finish_session.return_value = None

        auditron.run_resume("test.db")

        # Verify database operations
        mock_db.connect.assert_called_once_with("test.db")
        mock_db.ensure_schema.assert_called_once_with(temp_db)
        mock_db.get_unfinished_session.assert_called_once_with(temp_db)
        mock_db.get_hosts.assert_called_once_with(temp_db)
        mock_db.finish_session.assert_called_once_with(temp_db, 2)

        # Verify checks were run
        mock_run_all_checks.assert_called_once()

    @patch("auditron.run_all_checks")
    @patch("auditron.db")
    @patch("builtins.print")
    def test_run_resume_no_unfinished_session(
        self, mock_print, mock_db, mock_run_all_checks, temp_db
    ):
        """Test run_resume when there's no unfinished session."""
        # Setup mocks
        mock_db.connect.return_value = temp_db
        mock_db.ensure_schema.return_value = None
        mock_db.get_unfinished_session.return_value = None

        auditron.run_resume("test.db")

        # Verify appropriate message was printed
        mock_print.assert_called_once_with("No unfinished session found.")

        # Verify no checks were run
        mock_run_all_checks.assert_not_called()


class TestMainFunction:
    """Test main function."""

    @patch("auditron.run_mode")
    @patch("auditron.parse_cli")
    def test_main_fresh_mode(self, mock_parse_cli, mock_run_mode):
        """Test main function with fresh mode."""
        mock_parse_cli.return_value = ("fresh", "test.db")

        auditron.main()

        mock_parse_cli.assert_called_once()
        mock_run_mode.assert_called_once_with("test.db", "new")

    @patch("auditron.run_resume")
    @patch("auditron.parse_cli")
    def test_main_resume_mode(self, mock_parse_cli, mock_run_resume):
        """Test main function with resume mode."""
        mock_parse_cli.return_value = ("resume", "test.db")

        auditron.main()

        mock_parse_cli.assert_called_once()
        mock_run_resume.assert_called_once_with("test.db")

    @patch("auditron.parse_cli")
    def test_main_handles_exceptions(self, mock_parse_cli):
        """Test that main function handles exceptions gracefully."""
        mock_parse_cli.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            auditron.main()


class TestAuditContextCreation:
    """Test AuditContext creation in orchestrator functions."""

    @patch("auditron.run_all_checks")
    @patch("auditron.SSHClient")
    @patch("auditron.db")
    @patch("auditron.time")
    def test_audit_context_has_correct_attributes(
        self, mock_time, mock_db, mock_ssh_client_class, mock_run_all_checks, temp_db
    ):
        """Test that AuditContext is created with correct attributes."""
        # Setup mocks
        mock_db.connect.return_value = temp_db
        mock_db.ensure_schema.return_value = None
        mock_db.new_session.return_value = 42
        mock_db.get_hosts.return_value = [
            {"id": 1, "hostname": "test-host", "ip": "192.168.1.100"}
        ]
        mock_db.finish_session.return_value = None

        mock_ssh_instance = Mock()
        mock_ssh_client_class.return_value = mock_ssh_instance

        def capture_context(ctx):
            # Verify context attributes
            assert ctx.host["id"] == 1
            assert ctx.host["hostname"] == "test-host"
            assert ctx.ssh == mock_ssh_instance
            assert ctx.db == temp_db
            assert ctx.limits == {}
            assert ctx.clock == mock_time
            assert ctx.session_id == 42

        mock_run_all_checks.side_effect = capture_context

        auditron.run_mode("test.db", "new")
