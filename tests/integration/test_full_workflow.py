"""Integration tests for full Auditron workflow."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import auditron
from utils import db
from utils.ssh_runner import SSHResult


@pytest.mark.integration
class TestFullWorkflow:
    """Test complete Auditron workflow from start to finish."""

    def test_fresh_run_complete_workflow(self):
        """Test a complete fresh run workflow."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup database with test host
            conn = db.connect(db_path)
            db.ensure_schema(conn)
            conn.execute(
                "INSERT INTO hosts (hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("test-host", "192.168.1.100", "root", "/tmp/test_key", 22, 1),
            )
            conn.commit()
            conn.close()

            # Mock SSH operations to return realistic data
            with patch("auditron.SSHClient") as mock_ssh_class:
                mock_ssh = Mock()
                mock_ssh.which.return_value = True

                # Mock responses for different commands
                def mock_run(command, **kwargs):
                    if "os-release" in command or "centos-release" in command:
                        return SSHResult(0, "CentOS Linux|7|centos", "")
                    elif "uname" in command:
                        return SSHResult(0, "Linux 3.10.0-1160.el7.x86_64", "")
                    elif "ss -" in command:
                        return SSHResult(
                            0,
                            'tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=1234,fd=3))',
                            "",
                        )
                    elif "ps " in command:
                        return SSHResult(
                            0,
                            "PID PPID USER STIME ETIME CMD\n1 0 root Jan01 01:23:45 /sbin/init",
                            "",
                        )
                    elif "ip route" in command:
                        return SSHResult(0, "default via 192.168.1.1 dev eth0", "")
                    elif "rpm -qa" in command:
                        return SSHResult(0, "bash-4.2.46-34.el7.x86_64 1234567890", "")
                    elif "rpm -Va" in command:
                        return SSHResult(0, "SM5DLUGT. /etc/ssh/sshd_config", "")
                    else:
                        return SSHResult(0, "mock output", "")

                mock_ssh.run.side_effect = mock_run
                mock_ssh_class.return_value = mock_ssh

                # Run fresh workflow
                auditron.run_mode(db_path, "new")

            # Verify results
            conn = db.connect(db_path)

            # Check session was created and finished
            sessions = conn.execute("SELECT mode, finished_at FROM sessions").fetchall()
            assert len(sessions) == 1
            assert sessions[0][0] == "new"
            assert sessions[0][1] is not None  # Should be finished

            # Check that checks were run
            check_runs = conn.execute(
                "SELECT check_name, status FROM check_runs"
            ).fetchall()
            check_names = {row[0] for row in check_runs}
            expected_checks = {
                "osinfo",
                "processes",
                "routes",
                "rpm_inventory",
                "rpm_verify",
                "sockets",
            }
            assert expected_checks.issubset(check_names)

            # Check that data was collected
            os_info = conn.execute("SELECT name FROM os_info").fetchone()
            assert os_info is not None
            assert "CentOS" in os_info[0]

            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_resume_workflow(self):
        """Test resume workflow with unfinished session."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup database with test host and unfinished session
            conn = db.connect(db_path)
            db.ensure_schema(conn)

            # Add host
            conn.execute(
                "INSERT INTO hosts (hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("test-host", "192.168.1.100", "root", "/tmp/test_key", 22, 1),
            )

            # Add unfinished session
            conn.execute(
                "INSERT INTO sessions (started_at, finished_at, mode) "
                "VALUES (?, ?, ?)",
                ("2022-01-01T00:00:00Z", None, "resume"),
            )
            conn.commit()
            conn.close()

            # Mock SSH operations
            with patch("auditron.SSHClient") as mock_ssh_class:
                mock_ssh = Mock()
                mock_ssh.which.return_value = True
                mock_ssh.run.return_value = SSHResult(0, "mock output", "")
                mock_ssh_class.return_value = mock_ssh

                # Run resume workflow
                auditron.run_resume(db_path)

            # Verify session was completed
            conn = db.connect(db_path)
            session = conn.execute(
                "SELECT finished_at FROM sessions WHERE mode = 'resume'"
            ).fetchone()
            assert session[0] is not None  # Should now be finished
            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_no_hosts_workflow(self):
        """Test workflow when no hosts are configured."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup empty database (no hosts)
            conn = db.connect(db_path)
            db.ensure_schema(conn)
            conn.close()

            # Run fresh workflow
            auditron.run_mode(db_path, "new")

            # Verify session was created and finished even with no hosts
            conn = db.connect(db_path)
            sessions = conn.execute("SELECT mode, finished_at FROM sessions").fetchall()
            assert len(sessions) == 1
            assert sessions[0][0] == "new"
            assert sessions[0][1] is not None

            # Should be no check runs since no hosts
            check_runs = conn.execute("SELECT COUNT(*) FROM check_runs").fetchone()
            assert check_runs[0] == 0
            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_ssh_failure_handling(self):
        """Test workflow handles SSH failures gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Setup database with test host
            conn = db.connect(db_path)
            db.ensure_schema(conn)
            conn.execute(
                "INSERT INTO hosts (hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("test-host", "192.168.1.100", "root", "/tmp/test_key", 22, 1),
            )
            conn.commit()
            conn.close()

            # Mock SSH to simulate failures
            with patch("auditron.SSHClient") as mock_ssh_class:
                mock_ssh = Mock()
                mock_ssh.which.return_value = True

                # Simulate command failures
                def mock_run_with_failures(command, **kwargs):
                    if "os-release" in command:
                        return SSHResult(1, "", "Permission denied")
                    else:
                        return SSHResult(0, "success", "")

                mock_ssh.run.side_effect = mock_run_with_failures
                mock_ssh_class.return_value = mock_ssh

                # Should not raise exceptions despite SSH failures
                auditron.run_mode(db_path, "new")

            # Verify errors were recorded
            conn = db.connect(db_path)
            errors = conn.execute("SELECT stderr FROM errors").fetchall()
            assert len(errors) > 0
            assert any("Permission denied" in error[0] for error in errors)

            # Session should still be finished
            session = conn.execute("SELECT finished_at FROM sessions").fetchone()
            assert session[0] is not None
            conn.close()

        finally:
            Path(db_path).unlink(missing_ok=True)


@pytest.mark.integration
class TestDatabaseConsistency:
    """Test database consistency across operations."""

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = db.connect(db_path)
            db.ensure_schema(conn)

            # Try to insert check_run without valid host - should fail
            with pytest.raises(Exception):  # SQLite integrity error
                conn.execute(
                    "INSERT INTO check_runs (session_id, host_id, check_name, status) "
                    "VALUES (?, ?, ?, ?)",
                    (1, 999, "test", "SUCCESS"),  # host_id 999 doesn't exist
                )
                conn.commit()

            conn.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_cascade_deletes(self):
        """Test that cascade deletes work properly."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = db.connect(db_path)
            db.ensure_schema(conn)

            # Add host and session
            conn.execute(
                "INSERT INTO hosts (id, hostname, ip, ssh_user, ssh_port, use_sudo) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (1, "test-host", "192.168.1.100", "root", 22, 1),
            )
            session_id = db.new_session(conn, "new")

            # Add check run and error
            check_run_id = db.start_check(conn, session_id, 1, "test_check")
            db.record_error(conn, check_run_id, "ssh", "Connection failed", 255)

            # Verify data exists
            check_runs = conn.execute("SELECT COUNT(*) FROM check_runs").fetchone()[0]
            errors = conn.execute("SELECT COUNT(*) FROM errors").fetchone()[0]
            assert check_runs == 1
            assert errors == 1

            # Delete session - should cascade
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

            # Check runs and errors should be deleted
            check_runs = conn.execute("SELECT COUNT(*) FROM check_runs").fetchone()[0]
            errors = conn.execute("SELECT COUNT(*) FROM errors").fetchone()[0]
            assert check_runs == 0
            assert errors == 0

            conn.close()
        finally:
            Path(db_path).unlink(missing_ok=True)
