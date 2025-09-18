import os
import sqlite3
import time
from typing import Optional

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "docs", "schema.sql"
)


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Apply schema idempotently from docs/schema.sql"""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def get_hosts(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute(
        "SELECT id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo FROM hosts ORDER BY id"
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_unfinished_session(conn: sqlite3.Connection) -> Optional[int]:
    cur = conn.execute(
        "SELECT id FROM sessions WHERE finished_at IS NULL ORDER BY id DESC LIMIT 1"
    )
    row = cur.fetchone()
    return int(row[0]) if row else None


def new_session(conn: sqlite3.Connection, mode: str) -> int:
    conn.execute("INSERT INTO sessions(started_at, mode) VALUES (?, ?)", (ts(), mode))
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def finish_session(conn: sqlite3.Connection, session_id: int) -> None:
    conn.execute("UPDATE sessions SET finished_at=? WHERE id=?", (ts(), session_id))
    conn.commit()


def start_check(
    conn: sqlite3.Connection, session_id: Optional[int], host_id: int, check_name: str
) -> int:
    conn.execute(
        "INSERT INTO check_runs(session_id, host_id, check_name, started_at, status) VALUES (?, ?, ?, ?, ?)",
        (session_id, host_id, check_name, ts(), "SUCCESS"),
    )
    conn.commit()
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def mark_check(
    conn: sqlite3.Connection,
    check_run_id: int,
    status: str,
    reason: Optional[str] = None,
) -> None:
    conn.execute(
        "UPDATE check_runs SET finished_at=?, status=?, reason=? WHERE id=?",
        (ts(), status, reason, check_run_id),
    )
    conn.commit()


def record_error(
    conn: sqlite3.Connection,
    check_run_id: int,
    stage: str,
    stderr: str,
    exit_code: Optional[int],
) -> None:
    conn.execute(
        "INSERT INTO errors(check_run_id, stage, stderr, exit_code) VALUES (?, ?, ?, ?)",
        (check_run_id, stage, stderr, exit_code),
    )
    conn.commit()


def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
