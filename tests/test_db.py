"""Unit tests for database utilities."""

import sqlite3
import tempfile
from pathlib import Path

from utils import db


class TestDatabaseConnection:
    """Test database connection and schema management."""

    def test_connect_creates_connection(self):
        """Test that connect() creates a valid SQLite connection."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = db.connect(db_path)
            assert isinstance(conn, sqlite3.Connection)

            # Verify foreign keys are enabled
            result = conn.execute("PRAGMA foreign_keys").fetchone()
            assert result[0] == 1

            conn.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_ensure_schema_creates_tables(self, temp_db):
        """Test that ensure_schema creates all required tables."""
        # Get list of tables
        tables = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {row[0] for row in tables}

        expected_tables = {
            "hosts",
            "sessions",
            "check_runs",
            "errors",
            "global_defaults",
            "host_overrides",
            "rpm_packages",
            "file_meta",
            "file_snapshots",
            "rpm_verified_files",
            "users",
            "groups",
            "bash_history",
            "login_events",
            "listen_sockets",
            "processes",
            "proc_open_files",
            "services",
            "nmap_results",
            "resource_snapshots",
            "disk_usage",
            "os_info",
            "firewall_state",
            "net_interfaces",
            "hw_pci",
            "hw_usb",
            "hw_block",
            "routing_state",
        }

        assert expected_tables.issubset(table_names)

    def test_ensure_schema_idempotent(self, temp_db):
        """Test that ensure_schema can be called multiple times safely."""
        # Call ensure_schema again
        db.ensure_schema(temp_db)

        # Should not raise an error and tables should still exist
        tables = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert len(tables) >= 20  # We expect many tables


class TestSessionManagement:
    """Test session creation and management."""

    def test_new_session_creates_session(self, temp_db):
        """Test creating a new session."""
        session_id = db.new_session(temp_db, "new")

        assert isinstance(session_id, int)
        assert session_id > 0

        # Verify session was created in database
        session = temp_db.execute(
            "SELECT id, mode, started_at, finished_at FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()

        assert session is not None
        assert session[0] == session_id
        assert session[1] == "new"
        assert session[2] is not None  # started_at should be set
        assert session[3] is None  # finished_at should be NULL

    def test_finish_session_updates_timestamp(self, temp_db):
        """Test finishing a session updates the timestamp."""
        session_id = db.new_session(temp_db, "resume")

        db.finish_session(temp_db, session_id)

        session = temp_db.execute(
            "SELECT finished_at FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()

        assert session[0] is not None  # finished_at should now be set

    def test_get_unfinished_session_returns_latest(self, populated_db):
        """Test getting the latest unfinished session."""
        session_id = db.get_unfinished_session(populated_db)
        assert session_id == 2  # Session 2 is unfinished in our fixture

    def test_get_unfinished_session_returns_none_when_all_finished(self, temp_db):
        """Test that get_unfinished_session returns None when all sessions are finished."""
        session_id = db.new_session(temp_db, "new")
        db.finish_session(temp_db, session_id)

        unfinished = db.get_unfinished_session(temp_db)
        assert unfinished is None


class TestHostManagement:
    """Test host retrieval and management."""

    def test_get_hosts_returns_all_hosts(self, populated_db):
        """Test that get_hosts returns all configured hosts."""
        hosts = db.get_hosts(populated_db)

        assert len(hosts) == 3
        assert all(isinstance(host, dict) for host in hosts)

        # Check first host
        host1 = hosts[0]
        assert host1["id"] == 1
        assert host1["hostname"] == "host1"
        assert host1["ip"] == "192.168.1.10"
        assert host1["ssh_user"] == "root"
        assert host1["ssh_port"] == 22
        assert host1["use_sudo"] == 1

    def test_get_hosts_returns_empty_list_when_no_hosts(self, temp_db):
        """Test that get_hosts returns empty list when no hosts configured."""
        hosts = db.get_hosts(temp_db)
        assert hosts == []


class TestCheckRunManagement:
    """Test check run tracking."""

    def test_start_check_creates_check_run(self, temp_db, sample_host):
        """Test starting a check creates a check run record."""
        # Insert sample host
        temp_db.execute(
            "INSERT INTO hosts (id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                sample_host["id"],
                sample_host["hostname"],
                sample_host["ip"],
                sample_host["ssh_user"],
                sample_host["ssh_key_path"],
                sample_host["ssh_port"],
                sample_host["use_sudo"],
            ),
        )
        temp_db.commit()

        session_id = db.new_session(temp_db, "new")
        check_run_id = db.start_check(temp_db, session_id, sample_host["id"], "osinfo")

        assert isinstance(check_run_id, int)
        assert check_run_id > 0

        # Verify check run was created
        check_run = temp_db.execute(
            "SELECT session_id, host_id, check_name, status FROM check_runs WHERE id = ?",
            (check_run_id,),
        ).fetchone()

        assert check_run[0] == session_id
        assert check_run[1] == sample_host["id"]
        assert check_run[2] == "osinfo"
        assert check_run[3] == "SUCCESS"  # Default status

    def test_mark_check_updates_status(self, temp_db, sample_host):
        """Test marking a check updates its status."""
        # Setup
        temp_db.execute(
            "INSERT INTO hosts (id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                sample_host["id"],
                sample_host["hostname"],
                sample_host["ip"],
                sample_host["ssh_user"],
                sample_host["ssh_key_path"],
                sample_host["ssh_port"],
                sample_host["use_sudo"],
            ),
        )
        temp_db.commit()

        session_id = db.new_session(temp_db, "new")
        check_run_id = db.start_check(temp_db, session_id, sample_host["id"], "osinfo")

        # Mark as error
        db.mark_check(temp_db, check_run_id, "ERROR", "Test failure")

        # Verify update
        check_run = temp_db.execute(
            "SELECT status, reason, finished_at FROM check_runs WHERE id = ?",
            (check_run_id,),
        ).fetchone()

        assert check_run[0] == "ERROR"
        assert check_run[1] == "Test failure"
        assert check_run[2] is not None  # finished_at should be set

    def test_record_error_creates_error_record(self, temp_db, sample_host):
        """Test recording an error creates an error record."""
        # Setup
        temp_db.execute(
            "INSERT INTO hosts (id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                sample_host["id"],
                sample_host["hostname"],
                sample_host["ip"],
                sample_host["ssh_user"],
                sample_host["ssh_key_path"],
                sample_host["ssh_port"],
                sample_host["use_sudo"],
            ),
        )
        temp_db.commit()

        session_id = db.new_session(temp_db, "new")
        check_run_id = db.start_check(temp_db, session_id, sample_host["id"], "osinfo")

        # Record error
        db.record_error(temp_db, check_run_id, "ssh", "Connection refused", 255)

        # Verify error was recorded
        error = temp_db.execute(
            "SELECT check_run_id, stage, stderr, exit_code FROM errors WHERE check_run_id = ?",
            (check_run_id,),
        ).fetchone()

        assert error[0] == check_run_id
        assert error[1] == "ssh"
        assert error[2] == "Connection refused"
        assert error[3] == 255


class TestTimestampFunction:
    """Test timestamp generation."""

    def test_ts_returns_iso_format(self):
        """Test that ts() returns ISO format timestamp."""
        timestamp = db.ts()

        # Should match pattern YYYY-MM-DDTHH:MM:SSZ
        assert len(timestamp) == 20
        assert timestamp.endswith("Z")
        assert "T" in timestamp

        # Should be parseable as ISO format
        import datetime

        parsed = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None
