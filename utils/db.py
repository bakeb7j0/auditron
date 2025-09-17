import os, sqlite3, time

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "schema.sql")

def connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def ensure_schema(conn: sqlite3.Connection):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

def get_hosts(conn):
    cur = conn.execute("SELECT id, hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo FROM hosts ORDER BY id")
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def get_unfinished_session(conn):
    cur = conn.execute("SELECT id FROM sessions WHERE finished_at IS NULL ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    return row[0] if row else None

def new_session(conn, mode: str):
    conn.execute("INSERT INTO sessions(started_at, mode) VALUES (?, ?)",
                 (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), mode))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

def finish_session(conn, session_id: int):
    conn.execute("UPDATE sessions SET finished_at=? WHERE id=?", (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), session_id))
    conn.commit()

def start_check(conn, session_id: int, host_id: int, check_name: str):
    conn.execute(
        "INSERT INTO check_runs(session_id, host_id, check_name, started_at, status) VALUES (?, ?, ?, ?, ?)",
        (session_id, host_id, check_name, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "SUCCESS")
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

def mark_check(conn, check_run_id: int, status: str, reason: str | None = None):
    conn.execute("UPDATE check_runs SET finished_at=?, status=?, reason=? WHERE id=?",
                 (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), status, reason, check_run_id))
    conn.commit()

def record_error(conn, check_run_id: int, stage: str, stderr: str, exit_code: int | None):
    conn.execute("INSERT INTO errors(check_run_id, stage, stderr, exit_code) VALUES (?, ?, ?, ?)",
                 (check_run_id, stage, stderr, exit_code))
    conn.commit()
