"""Shared pytest fixtures for Auditron tests."""

import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import Mock

import pytest

from strategies.base import AuditContext
from utils import db
from utils.ssh_runner import SSHClient, SSHResult


@pytest.fixture
def temp_db() -> Generator[sqlite3.Connection, None, None]:
    """Create a temporary SQLite database with schema applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = db.connect(db_path)
        db.ensure_schema(conn)
        yield conn
    finally:
        conn.close()
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_host() -> Dict[str, Any]:
    """Sample host configuration for testing."""
    return {
        "id": 1,
        "hostname": "test-host",
        "ip": "192.168.1.100",
        "ssh_user": "root",
        "ssh_key_path": "/tmp/test_key",
        "ssh_port": 22,
        "use_sudo": 1,
    }


@pytest.fixture
def mock_ssh_client() -> Mock:
    """Mock SSH client that returns successful results by default."""
    mock = Mock(spec=SSHClient)
    mock.which.return_value = True
    mock.run.return_value = SSHResult(rc=0, out="mock output", err="")
    mock.host = {"hostname": "test-host", "ip": "192.168.1.100"}
    return mock


@pytest.fixture
def mock_failing_ssh_client() -> Mock:
    """Mock SSH client that returns failure results."""
    mock = Mock(spec=SSHClient)
    mock.which.return_value = False
    mock.run.return_value = SSHResult(rc=1, out="", err="command failed")
    mock.host = {"hostname": "test-host", "ip": "192.168.1.100"}
    return mock


@pytest.fixture
def mock_clock() -> Mock:
    """Mock clock module for consistent timestamps."""
    mock = Mock()
    mock.time.return_value = 1640995200.0  # 2022-01-01 00:00:00 UTC
    mock.gmtime.return_value = time.struct_time((2022, 1, 1, 0, 0, 0, 5, 1, 0))
    mock.strftime.return_value = "2022-01-01T00:00:00Z"
    return mock


@pytest.fixture
def audit_context(
    temp_db: sqlite3.Connection,
    sample_host: Dict[str, Any],
    mock_ssh_client: Mock,
    mock_clock: Mock,
) -> AuditContext:
    """Create a complete AuditContext for testing strategies."""
    # Insert sample host into database
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

    return AuditContext(
        host=sample_host,
        ssh=mock_ssh_client,
        db=temp_db,
        limits={},
        clock=mock_clock,
        session_id=session_id,
    )


@pytest.fixture
def populated_db(temp_db: sqlite3.Connection) -> sqlite3.Connection:
    """Database with sample hosts and sessions for testing."""
    # Insert sample hosts
    hosts_data = [
        (1, "host1", "192.168.1.10", "root", "/tmp/key1", 22, 1),
        (2, "host2", "192.168.1.20", "admin", "/tmp/key2", 2222, 0),
        (3, "host3", "192.168.1.30", "user", None, 22, 1),
    ]

    for host_data in hosts_data:
        temp_db.execute(
            "INSERT INTO hosts (id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            host_data,
        )

    # Insert sample sessions
    temp_db.execute(
        "INSERT INTO sessions (id, started_at, finished_at, mode) "
        "VALUES (1, '2022-01-01T00:00:00Z', '2022-01-01T01:00:00Z', 'new')"
    )
    temp_db.execute(
        "INSERT INTO sessions (id, started_at, finished_at, mode) "
        "VALUES (2, '2022-01-02T00:00:00Z', NULL, 'resume')"
    )

    # Insert sample check runs
    temp_db.execute(
        "INSERT INTO check_runs (id, session_id, host_id, check_name, started_at, finished_at, status, reason) "
        "VALUES (1, 1, 1, 'osinfo', '2022-01-01T00:00:00Z', '2022-01-01T00:01:00Z', 'SUCCESS', NULL)"
    )
    temp_db.execute(
        "INSERT INTO check_runs (id, session_id, host_id, check_name, started_at, finished_at, status, reason) "
        "VALUES (2, 1, 1, 'sockets', '2022-01-01T00:01:00Z', '2022-01-01T00:02:00Z', 'ERROR', 'Connection failed')"
    )

    temp_db.commit()
    return temp_db


@pytest.fixture
def rpm_verify_output() -> str:
    """Sample rpm verify output for parser testing."""
    return """SM5DLUGT.  c /etc/ssh/sshd_config
..5...... /usr/bin/ssh
.M....... /var/log/messages
S.5....T. /etc/hosts
"""


@pytest.fixture
def ss_listen_output() -> str:
    """Sample ss -tuln output for parser testing."""
    return """tcp   LISTEN 0      128          0.0.0.0:22        0.0.0.0:*    users:(("sshd",pid=1234,fd=3))
tcp   LISTEN 0      80           0.0.0.0:80        0.0.0.0:*    users:(("httpd",pid=5678,fd=4))
udp   UNCONN 0      0            0.0.0.0:53        0.0.0.0:*    users:(("systemd-resolve",pid=9012,fd=12))
tcp   LISTEN 0      128             [::]:22           [::]:*    users:(("sshd",pid=1234,fd=4))
"""


@pytest.fixture
def ps_output() -> str:
    """Sample ps output for parser testing."""
    return """    1     0 root     Mon Jan  1 00:00:00 2022 01:23:45 /sbin/init
 1234     1 root     Mon Jan  1 00:00:01 2022    45:32 /usr/sbin/sshd -D
 5678  1234 user     Mon Jan  1 12:34:00 2022    00:15 sshd: user@pts/0
 9012     1 systemd+ Mon Jan  1 00:00:02 2022 01:20:11 /usr/lib/systemd/systemd-resolved
"""


@pytest.fixture
def uname_output() -> str:
    """Sample uname output for testing."""
    return "Linux 3.10.0-1160.el7.x86_64 #1 SMP Mon Oct 19 16:18:59 UTC 2020 x86_64"


@pytest.fixture
def os_release_output() -> str:
    """Sample /etc/os-release output for testing."""
    return "CentOS Linux|7|centos"


@pytest.fixture
def ip_route_output() -> str:
    """Sample ip route output for testing."""
    return """default via 192.168.1.1 dev eth0 proto dhcp metric 100
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100 metric 100
169.254.0.0/16 dev eth0 scope link metric 1002
"""
